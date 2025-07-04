from google.genai import Client
import asyncio
import re, json

async def extract_discharge_details(gemini_client: Client, file_resource) -> dict:
    prompt = (
        "Extract the following details from the discharge summary PDF: patient_name, diagnosis, admission_date, discharge_date. "
        "Return a JSON object with keys: type (set to 'discharge_summary'), patient_name, diagnosis, admission_date, discharge_date. "
        "If any field is missing, set its value to null."
    )
    response = gemini_client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[file_resource, prompt]
    )
    # Try to extract JSON from response

    text = response.text or ""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    # Fallback
    return {"type": "discharge_summary", "patient_name": None, "diagnosis": None, "admission_date": None, "discharge_date": None} 