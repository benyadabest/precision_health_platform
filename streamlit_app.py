import streamlit as st
import os
from hospital_pro_patient_facing_app_sdk import FoundryClient
from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient, Proentity, Vitals
from foundry_sdk_runtime.auth import UserTokenAuth
from foundry_sdk_runtime.types import ActionConfig, ActionMode, ReturnEditsMode
from datetime import date
from dotenv import load_dotenv
from foundry_client import client as ontology_client
from openai import OpenAI
from twilio.rest import Client as TwilioClient
import json
import pandas as pd
import streamlit.components.v1 as components

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("OPENAI_API_KEY environment variable not set. Please set it and restart.")
    st.stop()
client_ai = OpenAI(api_key=openai_api_key)

twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = TwilioClient(twilio_account_sid, twilio_auth_token)

st.title("Patient EHR Hub")


if 'patient_found' not in st.session_state:
    st.session_state['patient_found'] = None

st.subheader("Search Patient")

search_label = "Enter Patient Name:"
search_term = st.text_input(search_label)

search_button = st.button("Search")


foundry_token = os.getenv("FOUNDRY_TOKEN")
if not foundry_token:
    st.error("FOUNDRY_TOKEN environment variable not set. Please add it to your .env and restart.")
    st.stop()

try:
    auth = UserTokenAuth(
        hostname="https://benshvartsman1.usw-18.palantirfoundry.com",
        token=foundry_token
    )

    client = FoundryClient(
        auth=auth,
        hostname="https://benshvartsman1.usw-18.palantirfoundry.com"
    )

    PatientObjectService = client.ontology.objects.Patient
    if search_button and search_term:
        results = PatientObjectService.where(Patient.object_type.name == search_term).take(1)
        st.session_state['patient_found'] = results[0] if results else None

    patient_found = st.session_state['patient_found']
    if patient_found:
        st.subheader(f"{search_term}'s EHR")
        st.markdown("---")
        properties = vars(patient_found)
        col1, col2 = st.columns(2)
        count = 0
        for prop_name, prop_value in properties.items():
            if not prop_name.startswith('_') and prop_name not in ['rid', 'primary_key']:
                display_value = f"`{prop_value}`" if prop_value is not None else "_Not set_"
                if count % 2 == 0:
                    with col1:
                        st.markdown(f"**{prop_name.replace('_', ' ').title()}:** {display_value}")
                else:
                    with col2:
                        st.markdown(f"**{prop_name.replace('_', ' ').title()}:** {display_value}")
                count += 1
        
        st.markdown("---")
        st.subheader("Contribute to Positive Patient Outcomes through Voice AI")
        components.html("""
            <elevenlabs-convai agent-id="VQY3pQsQ3xceL0RrAI8N"></elevenlabs-convai>
            <script src="https://elevenlabs.io/convai-widget/index.js" async type="text/javascript"></script>
        """, height=100)

        st.markdown("---")
        with st.expander("Submit New Patient Reported Outcome", expanded=False):
            with st.form("new_pro_form", clear_on_submit=True):
                pro_free_text = st.text_area("Free Text Notes:")
                submitted = st.form_submit_button("Submit PRO")

                if submitted:
                    if not pro_free_text or not pro_free_text.strip():
                        st.error("Please enter your check-in notes before submitting.")
                    else:
                        try:
                            sentiment_resp = client_ai.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a healthcare assistant. Classify the sentiment of the following patient check-in note as Positive or Negative. Respond with only one word: Positive or Negative."},
                                    {"role": "user", "content": pro_free_text}
                                ]
                            )
                            sentiment = sentiment_resp.choices[0].message.content.strip()

                            symptoms_resp = client_ai.chat.completions.create(
                                model="gpt-3.5-turbo",
                                messages=[
                                    {"role": "system", "content": "You are a healthcare assistant. Extract all symptoms mentioned in the following patient check-in note. Return a JSON array of strings only. If no symptoms are mentioned, return [\"none\"]. No commentary or explanation."},
                                    {"role": "user", "content": pro_free_text}
                                ]
                            )
                            symptoms_str = symptoms_resp.choices[0].message.content.strip()
                            try:
                                symptoms = json.loads(symptoms_str)
                            except json.JSONDecodeError:
                                symptoms = ["none"]
                            if not symptoms:
                                symptoms = ["none"]

                            action_cfg = ActionConfig(
                                mode=ActionMode.VALIDATE_AND_EXECUTE,
                                return_edits=ReturnEditsMode.ALL,
                            )
                            response = ontology_client.ontology.actions.create_proentity(
                                action_config=action_cfg,
                                patient=patient_found.id,
                                submitted_at=date.today().isoformat(),
                                free_text=pro_free_text,
                                sentiment=sentiment,
                                symptoms=symptoms,
                            )
                            if response.validation.validation_result == "VALID":
                                st.success("PRO submitted successfully!")
                        except Exception as e:
                            st.error(f"Error during PRO submission: {e}")
                            st.exception(e)

        st.markdown("---")
        with st.expander("Submit New Daily Vitals", expanded=False):
            with st.form("new_vitals_form", clear_on_submit=True):
                hrv = st.number_input("Heart Rate Variability (HRV):", min_value=0, step=1)
                heart_rate = st.number_input("Heart Rate:", min_value=0, step=1)
                sleep_hours = st.number_input("Sleep Hours:", min_value=0.0, step=0.1, format="%.1f")
                submitted_vitals = st.form_submit_button("Submit Vitals")
                if submitted_vitals:
                    action_cfg_v = ActionConfig(
                        mode=ActionMode.VALIDATE_AND_EXECUTE,
                        return_edits=ReturnEditsMode.ALL,
                    )
                    try:
                        response_v = ontology_client.ontology.actions.create_vitals(
                            action_config=action_cfg_v,
                            date_=date.today(),
                            hrv=hrv,
                            sleep_hours=sleep_hours,
                            patient=patient_found.id,
                            heart_rate=heart_rate,
                        )
                        if response_v.validation.validation_result == "VALID":
                            st.success("Vitals submitted successfully!")
                            st.info("Click 'Search' again to refresh the vitals list.")
                        else:
                            st.error(f"Vitals submission failed validation: {response_v.validation.validation_result}")
                            try:
                                vd = response_v.validation._asdict(include_type_field=True)
                                st.write("Validation Details:")
                                st.json(vd)
                            except Exception as ex:
                                st.warning(f"Could not serialize validation details: {ex}")
                    except Exception as err_v:
                        st.error(f"Error during vitals submission: {err_v}")
                        st.exception(err_v)

        st.markdown("---")
        st.subheader("Patient Vitals Trend")
        try:
            vitals_list = list(client.ontology.objects.Vitals.where(Vitals.object_type.patient == patient_found.id).iterate())
            if vitals_list:
                records = [{
                    'date': v.date_,
                    'HRV': v.hrv,
                    'Heart Rate': v.heart_rate,
                    'Sleep Hours': v.sleep_hours
                } for v in vitals_list]
                df_v = pd.DataFrame(records)
                df_v['date'] = pd.to_datetime(df_v['date'])
                df_v = df_v.set_index('date').sort_index()
                st.line_chart(df_v)
            else:
                st.info("No vitals found for this patient.")
        except Exception as e:
            st.error(f"Error loading vitals: {e}")
        st.subheader("Linked Patient Reported Outcomes")
        try:
            linked_pro_entities_iterator = patient_found.proentities.iterate()
            linked_pro_entities = list(linked_pro_entities_iterator)
            
            if linked_pro_entities:
                for pro_entity in linked_pro_entities:
                    with st.container(border=True):
                        submitted_at = getattr(pro_entity, 'submittedAt', None)
                        sentiment = getattr(pro_entity, 'sentiment', None)
                        symptoms = getattr(pro_entity, 'symptoms', [])
                        free_text = getattr(pro_entity, 'freeText', None)

                        if sentiment:
                            st.markdown(f"**Sentiment:** {sentiment}")
                        
                        if symptoms:
                            symptom_str = ", ".join(symptoms)
                            st.markdown(f"**Symptoms:** {symptom_str}")
                        else:
                            st.markdown("**Symptoms:** _None reported_")

                        if free_text:
                            st.markdown("**Notes:**")
                            st.markdown(f"> {free_text}")
                        
                        linked_col1, linked_col2 = st.columns(2)
                        linked_count = 0
                        remaining_props_displayed = False
                        for linked_prop_name, linked_prop_value in vars(pro_entity).items():
                            if not linked_prop_name.startswith('_') and linked_prop_name not in ['rid', 'primary_key', 'id', 'submittedAt', 'sentiment', 'symptoms', 'freeText', 'patient']:
                                remaining_props_displayed = True
                                linked_display_value = f"`{linked_prop_value}`" if linked_prop_value is not None else "_Not set_"
                                if linked_count % 2 == 0:
                                    with linked_col1:
                                        st.markdown(f"**{linked_prop_name.replace('_', ' ').title()}:** {linked_display_value}")
                                else:
                                    with linked_col2:
                                        st.markdown(f"**{linked_prop_name.replace('_', ' ').title()}:** {linked_display_value}")
                                linked_count += 1
                        if not remaining_props_displayed:
                             st.markdown("_No other details available._")

            else:
                st.info("No linked PRO Entities found for this patient.")
                
        except AttributeError as attr_error:
             if 'proentities' in str(attr_error):
                 st.warning("Could not find the 'proentities' link. Please verify the link API name in the Ontology.")
             else:
                 st.warning(f"An attribute error occurred: {attr_error}")
        except Exception as link_error:
            st.error(f"An error occurred while fetching or displaying linked PRO Entities: {link_error}")
    
    elif search_button and not patient_found:
        st.warning(f"Could not find patient with name '{search_term}'.")
        st.session_state['patient_found'] = None

except Exception as e:
    st.error(f"An error occurred during setup or search:")
    st.exception(e)