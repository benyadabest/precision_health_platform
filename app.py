import os
import json
import logging
import hmac
import hashlib
from datetime import date
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv
from foundry_client import client as ontology_client


try: from openai import OpenAI, OpenAIError; OPENAI_AVAILABLE = True
except ImportError: logging.warning("OpenAI SDK not found."); OPENAI_AVAILABLE = False


from hospital_pro_patient_facing_app_sdk import FoundryClient, ontology
from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient
from foundry_sdk_runtime.auth import UserTokenAuth
from foundry_sdk_runtime.types import ActionConfig, ActionMode, ReturnEditsMode


load_dotenv()

EXPECTED_SECRET = os.getenv("ELEVENLABS_WEBHOOK_SECRET")
FOUNDRY_HOSTNAME = os.getenv("FOUNDRY_HOSTNAME")
FOUNDRY_TOKEN = os.getenv("FOUNDRY_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

handler = logging.StreamHandler(); formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'); handler.setFormatter(formatter)
app.logger.addHandler(handler); app.logger.setLevel(logging.INFO)

foundry_token = os.getenv("FOUNDRY_TOKEN")
auth = UserTokenAuth(
        hostname="https://benshvartsman1.usw-18.palantirfoundry.com",
        token=foundry_token
    )
foundry_client = FoundryClient(
        auth=auth,
        hostname="https://benshvartsman1.usw-18.palantirfoundry.com"
    )
app.logger.info(f"Foundry client initialized successfully for hostname: {FOUNDRY_HOSTNAME}")

openai_client = None
if OPENAI_AVAILABLE and OPENAI_API_KEY:
     try: openai_client = OpenAI(api_key=OPENAI_API_KEY); app.logger.info("OpenAI client initialized.")
     except Exception as e: app.logger.error(f"CRITICAL: Failed to initialize OpenAI client: {e}")


import time

def verify_signature_from_raw(raw_body, headers):
    if not EXPECTED_SECRET:
        app.logger.error("CRITICAL: ELEVENLABS_WEBHOOK_SECRET is not set.")
        abort(500, description="Webhook secret not configured on server")

    
    header_value = headers.get('ElevenLabs-Signature')
    if not header_value:
        app.logger.warning("Missing 'ElevenLabs-Signature' header.")
        abort(400, description="Missing signature header")

    timestamp = None
    signature_v0 = None
    try:
        items = header_value.split(',')
        for item in items:
            parts = item.split('=', 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key == 't':
                    timestamp = int(value)
                elif key == 'v0':
                    signature_v0 = value
        app.logger.info(f"Parsed timestamp: {timestamp}, Parsed v0 signature: {signature_v0[:5] if signature_v0 else 'None'}...")
    except Exception as e:
        app.logger.error(f"Failed to parse 'ElevenLabs-Signature' header value: {header_value}. Error: {e}")
        abort(400, description="Invalid signature header format")

    if timestamp is None or signature_v0 is None:
        app.logger.error(f"Could not extract timestamp or v0 signature from header: {header_value}")
        abort(400, description="Incomplete signature header (missing t or v0)")

    tolerance_seconds = 300
    current_time = int(time.time())
    if abs(current_time - timestamp) > tolerance_seconds:
        app.logger.warning(f"Signature timestamp ({timestamp}) outside tolerance window (current: {current_time}).")
        abort(403, description="Signature timestamp outside tolerance window")


    try:
        if isinstance(raw_body, bytes):
            signed_payload_string = f"{timestamp}.{raw_body.decode('utf-8')}"
        else:
            app.logger.error(f"Unexpected type for raw_body: {type(raw_body)}")
            abort(500, "Internal error processing request body for signature")
        app.logger.debug(f"Constructed signed_payload_string: {signed_payload_string[:50]}...")
    except UnicodeDecodeError as e:
         app.logger.error(f"Failed to decode raw_body as utf-8: {e}")
         abort(400, description="Invalid request body encoding for signature")

    try:
        hash_obj = hmac.new(
            EXPECTED_SECRET.encode('utf-8'),
            msg=signed_payload_string.encode('utf-8'),
            digestmod=hashlib.sha256
        )
        expected_signature = hash_obj.hexdigest()
        app.logger.info(f"Calculated expected signature: {expected_signature[:5]}...")
    except Exception as e:
        app.logger.error(f"Error during HMAC calculation: {e}")
        abort(500, description="Failed to calculate signature")

    if not hmac.compare_digest(expected_signature, signature_v0):
        app.logger.warning(f"Invalid signature comparison failed. Expected '{expected_signature[:5]}...', got v0 '{signature_v0[:5]}...'")
        abort(403, description="Invalid signature")

    app.logger.info("Webhook signature verified successfully."); return True


def get_ai_sentiment(text):
    if not openai_client or not text: return None
    try:
        app.logger.info("Requesting sentiment analysis from OpenAI...")
        sentiment_resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a healthcare assistant. Classify the sentiment of the following patient check-in note as Positive or Negative. Respond with only one word: Positive or Negative."},
                {"role": "user", "content": text}
            ]
        )
        sentiment = sentiment_resp.choices[0].message.content.strip()
        app.logger.info(f"OpenAI sentiment result: {sentiment}")
        return sentiment if sentiment in ["Positive", "Negative"] else None
    except Exception as e: app.logger.error(f"Error during sentiment analysis: {e}"); return None

def get_ai_symptoms(text):
    if not openai_client or not text: return ["none"]
    try:
        app.logger.info("Requesting symptom extraction from OpenAI...")
        symptoms_resp = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
             messages=[ 
                {"role": "system", "content": "You are a healthcare assistant. Extract all symptoms mentioned in the following patient check-in note. Return a JSON array of strings only. If no symptoms are mentioned, return [\"none\"]. No commentary or explanation."},
                {"role": "user", "content": text}
            ]
        )
        symptoms_str = symptoms_resp.choices[0].message.content.strip()
        app.logger.info(f"OpenAI symptoms result (raw): {symptoms_str}")
        try: symptoms = json.loads(symptoms_str); return symptoms if isinstance(symptoms, list) and symptoms else ["none"]
        except json.JSONDecodeError: app.logger.warning(f"OpenAI symptoms invalid JSON: {symptoms_str}"); return ["none"]
    except Exception as e: app.logger.error(f"Error during symptom extraction: {e}"); return ["none"]


def find_patient_by_name(name):
    # <<< Add explicit check log >>>
    from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient

    app.logger.info(f"Entering find_patient_by_name. Client available: {bool(foundry_client)}, Patient obj available: {bool(Patient)}")



    if not name or not isinstance(name, str) or not name.strip():
        app.logger.warning(f"Invalid or empty patient name received for search: '{name}' (type: {type(name)})")
        return None

    search_term = name.strip()
    app.logger.info(f"Attempting search using Streamlit logic with search_term: '{search_term}'")


    try:
        PatientObjectService = foundry_client.ontology.objects.Patient

        results = PatientObjectService.where(Patient.object_type.name == search_term).take(1)

        if len(results) == 1:
            found_patient_object = results[0]
            patient_identifier = found_patient_object.id
            found_name = getattr(found_patient_object, 'name', '[name property not found]')
            app.logger.info(f"Found unique patient matching Streamlit query logic: Name='{found_name}', Identifier='{patient_identifier}'")
            return patient_identifier
        elif len(results) == 0:
            app.logger.warning(f"No patient found matching Streamlit query logic for search_term: '{search_term}' (Searching Patient.object_type.name)")
            return None

    except Exception as e:
        app.logger.error(f"Error during patient search using Streamlit logic: {e}", exc_info=True)
        return None


def create_foundry_pro(patient_foundry_id, free_text_content, sentiment, symptoms):

    from foundry_sdk_runtime.types import ActionConfig, ActionMode, ReturnEditsMode

    if not ontology_client: 
         app.logger.error("Ontology client (ontology_client) unavailable for create_proentity.");
         return False

    if not isinstance(symptoms, list): symptoms = ["none"]
    if not symptoms: symptoms = ["none"]
    if not free_text_content and not sentiment and symptoms == ["none"]:
        app.logger.info("No meaningful data (text, sentiment, symptoms) for PROEntity creation.")
        return False

    try:
        action_cfg = ActionConfig(mode=ActionMode.VALIDATE_AND_EXECUTE, return_edits=ReturnEditsMode.ALL)
        app.logger.info(f"Attempting to create PROEntity for patient ID: {patient_foundry_id}")

        response = ontology_client.ontology.actions.create_proentity(
            action_config=action_cfg,
            patient=patient_foundry_id,
            submitted_at=date.today().isoformat(),
            free_text=free_text_content,
            sentiment=sentiment if sentiment == "Positive" else "Negative",
            symptoms=symptoms,
        )

        if response and hasattr(response, 'validation') and response.validation.validation_result == "VALID":
             app.logger.info(f"Successfully created PROEntity for patient ID: {patient_foundry_id}"); return True
        elif response and hasattr(response, 'validation'):
             app.logger.error(f"Foundry 'create_proentity' failed validation: {response.validation.validation_result}")
             try: vd = response.validation._asdict(include_type_field=True); app.logger.error(f"Validation Details: {json.dumps(vd)}")
             except Exception: pass
             return False
        else: app.logger.error("'create_proentity' call bad response structure."); return False
    except Exception as e: app.logger.error(f"Error during create_proentity: {e}", exc_info=True); return False


def create_foundry_vitals(patient_foundry_id, results):
    from foundry_sdk_runtime.types import ActionConfig, ActionMode, ReturnEditsMode

    if not foundry_client:
        app.logger.error("Foundry client unavailable for create_vitals.")
        return False

    hrv_obj = results.get("hrv")
    heart_rate_obj = results.get("heart_rate")
    sleep_hours_obj = results.get("sleep_hours")

    hrv_val_extracted = hrv_obj.get("value") if isinstance(hrv_obj, dict) else hrv_obj
    heart_rate_val_extracted = heart_rate_obj.get("value") if isinstance(heart_rate_obj, dict) else heart_rate_obj
    sleep_hours_val_extracted = sleep_hours_obj.get("value") if isinstance(sleep_hours_obj, dict) else sleep_hours_obj

    app.logger.info(f"Extracted Vitals - HRV: {hrv_val_extracted}, HR: {heart_rate_val_extracted}, Sleep: {sleep_hours_val_extracted}")


    hrv_val = 0
    if hrv_val_extracted is not None:
        try:
            hrv_val = int(float(hrv_val_extracted))
        except (ValueError, TypeError):
            app.logger.warning(f"Could not convert extracted HRV value '{hrv_val_extracted}' to integer. Defaulting to 0.")
            hrv_val = 0

    heart_rate_val = 0
    if heart_rate_val_extracted is not None:
        try:
            heart_rate_val = int(float(heart_rate_val_extracted))
        except (ValueError, TypeError):
            app.logger.warning(f"Could not convert extracted HR value '{heart_rate_val_extracted}' to integer. Defaulting to 0.")
            heart_rate_val = 0

    sleep_hours_val = 0.0
    if sleep_hours_val_extracted is not None:
        try:
            sleep_hours_val = float(sleep_hours_val_extracted)
        except (ValueError, TypeError):
            app.logger.warning(f"Could not convert extracted Sleep value '{sleep_hours_val_extracted}' to float. Defaulting to 0.0.")
            sleep_hours_val = 0.0

    try:
        if hrv_val > 0 or heart_rate_val > 0 or sleep_hours_val > 0:
            action_cfg_v = ActionConfig(mode=ActionMode.VALIDATE_AND_EXECUTE, return_edits=ReturnEditsMode.ALL)
            app.logger.info(f"Attempting to create Vitals for patient ID: {patient_foundry_id} with values HRV={hrv_val}, HR={heart_rate_val}, Sleep={sleep_hours_val}")
            response_v = ontology_client.ontology.actions.create_vitals(
                action_config=action_cfg_v, date_=date.today(), hrv=hrv_val,
                sleep_hours=sleep_hours_val, patient=patient_foundry_id, heart_rate=heart_rate_val,
            )
            if response_v and hasattr(response_v, 'validation') and response_v.validation.validation_result == "VALID":
                 app.logger.info(f"Successfully created Vitals for patient ID: {patient_foundry_id}"); return True
            elif response_v and hasattr(response_v, 'validation'):
                 app.logger.error(f"Foundry 'create_vitals' failed validation: {response_v.validation.validation_result}")
                 try: vd = response_v.validation._asdict(include_type_field=True); app.logger.error(f"Validation Details: {json.dumps(vd)}")
                 except Exception: pass
                 return False
            else: app.logger.error("Foundry 'create_vitals' call bad response structure."); return False
        else:
            app.logger.info(f"Skipping Vitals creation: All vital signs were zero after extraction/conversion (HRV={hrv_val}, HR={heart_rate_val}, Sleep={sleep_hours_val}).")
            return False
    except Exception as e: app.logger.error(f"Error during create_vitals action: {e}", exc_info=True); return False


@app.route('/webhook/elevenlabs/postcall', methods=['POST'])
def handle_elevenlabs_webhook():
    print(">>> HANDLE WEBHOOK CALLED <<<")
    app.logger.info("Received request on /webhook/elevenlabs/postcall")
    raw_body = request.get_data()

    if EXPECTED_SECRET:
        if not verify_signature_from_raw(raw_body, request.headers): return jsonify({"status": "error", "message": "Signature verification failed"}), 403
    else: app.logger.warning("Proceeding without signature verification.")

    try: data = json.loads(raw_body.decode('utf-8')); app.logger.info(f"Received top-level payload structure: {list(data.keys())}")
    except Exception as e: app.logger.error(f"JSON parsing error: {e}"); return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    actual_conversation_data = data.get('data')
    if not actual_conversation_data or not isinstance(actual_conversation_data, dict): app.logger.warning("Expected 'data' key missing or invalid."); return jsonify({"status": "success", "message": "Webhook invalid format."}), 200
    app.logger.info(f"Structure within 'data' key: {list(actual_conversation_data.keys())}")
    app.logger.debug(f"Content of 'data' key: {json.dumps(actual_conversation_data, indent=2)}")

    analysis = actual_conversation_data.get('analysis');
    data_collection_results = analysis.get('data_collection_results') if analysis else None
    if not data_collection_results: app.logger.info("No 'data_collection_results' found in nested data."); return jsonify({"status": "success", "message": "No data_collection_results."}), 200

    patient_name_string = None
    name_collection_object = data_collection_results.get("name")

    if isinstance(name_collection_object, dict):
        patient_name_string = name_collection_object.get("value")
        app.logger.info(f"Extracted patient name from dict ('value' field): '{patient_name_string}'")
    elif isinstance(name_collection_object, str):
        patient_name_string = name_collection_object
        app.logger.info(f"Extracted patient name directly as string: '{patient_name_string}'")
    else:
        if name_collection_object is not None:
             app.logger.warning(f"Unexpected data type for 'name' in data_collection_results: {type(name_collection_object)}")

    if not patient_name_string or not patient_name_string.strip():
        app.logger.error("Patient name could not be extracted or is empty after processing data_collection_results['name'].");
        app.logger.info(f"Original data for 'name' key: {name_collection_object}")
        return jsonify({"status": "error", "message": "Patient name could not be extracted."}), 400

    app.logger.info(f"PRE-SEARCH CHECK -> Client type: {type(foundry_client)}, Patient class type: {type(Patient)}")
    patient_id = find_patient_by_name(patient_name_string)

    if patient_id:
        app.logger.info(f"Proceeding with actions for patient ID: {patient_id}")

        free_text_object = data_collection_results.get("free_text")
        if isinstance(free_text_object, dict):
            free_text_string = free_text_object.get("value"); 
            app.logger.info(f"Extracted free_text from dict ('value' field): '{free_text_string[:50]}...'")
        elif isinstance(free_text_object, str):
            free_text_string = free_text_object;
            app.logger.info(f"Extracted free_text as string: '{free_text_string[:50]}...'")
        else:
            app.logger.warning(f"Unexpected data type for 'free_text' in data_collection_results: {type(free_text_object)}")
        ai_sentiment = None; ai_symptoms = ["none"]
        if free_text_string and openai_client: pass # AI calls
        pro_created = create_foundry_pro(patient_id, free_text_string, ai_sentiment, ai_symptoms)
        vitals_created = create_foundry_vitals(patient_id, data_collection_results)
        if pro_created or vitals_created: return jsonify({"status": "success", "message": f"Webhook processed for '{patient_name_string}'. Actions attempted."}), 200
        else: return jsonify({"status": "success", "message": f"Webhook processed for '{patient_name_string}', but no objects created."}), 200
    else:
        app.logger.warning(f"No unique patient found for name '{patient_name_string}'. No actions taken.")
        return jsonify({"status": "success", "message": f"Could not uniquely identify patient '{patient_name_string}'."}), 200

if __name__ == '__main__':
    log = app.logger if app else logging
    if not EXPECTED_SECRET: log.warning("WARNING: ELEVENLABS_WEBHOOK_SECRET not set! Verification SKIPPED.")
    else: log.info("ELEVENLABS_WEBHOOK_SECRET found. Signature verification enabled.")
    if not OPENAI_API_KEY: log.warning("WARNING: OPENAI_API_KEY not set! AI analysis disabled.")
    else: log.info("OPENAI_API_KEY found. AI analysis enabled.")

    app.run(host='0.0.0.0', port=5000, debug=True)