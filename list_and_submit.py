from datetime import date
from pprint import pprint

from foundry_client import client
from foundry_sdk_runtime.types import ActionConfig, ActionMode, ReturnEditsMode
from hospital_pro_patient_facing_app_sdk.ontology.objects import Patient


def list_patients():
    patients = list(client.ontology.objects.Patient.iterate())
    pprint(patients)


def submit_demo_pro(patient_id: str):
    action_cfg = ActionConfig(
        mode=ActionMode.VALIDATE_AND_EXECUTE,
        return_edits=ReturnEditsMode.ALL,
    )
    response = client.ontology.actions.create_proentity(
        action_config=action_cfg,
        patient=patient_id,
        submitted_at=date.today().isoformat(),
        free_text="Demo PRO via Python SDK",
        sentiment="Positive",
        symptoms=["fatigue", "headache"],
    )

    print("Validation:", response.validation.validation_result)
    if hasattr(response, 'edits') and response.edits.type == "edits":
        # Print the edits response to inspect created/updated objects
        print("Edits response:", response.edits)


if __name__ == "__main__":
    print("=== Patients ===")
    list_patients()

    print("\n=== Submit PRO for PT001 ===")
    submit_demo_pro("PT001")