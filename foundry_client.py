import os
from dotenv import load_dotenv
load_dotenv()
from hospital_pro_patient_facing_app_sdk import FoundryClient
from foundry_sdk_runtime.auth import UserTokenAuth

foundry_token = os.getenv("FOUNDRY_TOKEN")
if not foundry_token:
    raise RuntimeError("FOUNDRY_TOKEN not set; please add it to your .env or environment variables")

foundry_host = os.getenv("FOUNDRY_HOSTNAME") or os.getenv("FOUNDRY_HOST")
if not foundry_host:
    raise RuntimeError("FOUNDRY_HOSTNAME not set; please add it to your .env or environment variables")


auth = UserTokenAuth(
    hostname=foundry_host,
    token=foundry_token
)

client = FoundryClient(auth=auth, hostname=foundry_host)

PatientObject = client.ontology.objects.Patient
