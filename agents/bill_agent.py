from google.genai import Client
import re, json
import asyncio

async def extract_bill_details(gemini_client: Client, file_resource) -> dict:
    prompt = (
        "Extract the following details from the bill PDF: hospital_name, total_amount, date_of_service. "
        "Return a JSON object with keys: type (set to 'bill'), hospital_name, total_amount, date_of_service. "
        "If any field is missing, set its value to null."
    )
    response = await asyncio.to_thread(
        gemini_client.models.generate_content,
        model="gemini-1.5-flash",
        contents=[file_resource, prompt]
    )
    text = response.text or ""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    # Fallback
    return {"type": "bill", "hospital_name": None, "total_amount": None, "date_of_service": None} 