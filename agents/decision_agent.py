import json
import re

def final_decision_agent(gemini_client, documents: list, validation: dict) -> dict:
    data = {
        "documents": documents,
    }
    prompt = f"""
You are an insurance claim processor.

Given the following structured data about a claim:

{json.dumps(data, indent=2)}

Evaluate the claim based on:
- Presence of required documents (bill, discharge_summary)
- Validity and consistency of data (e.g., dates match, no missing fields)

Return a JSON object in this format:

{{
  "documents": [...],
  "validation": {{
    "missing_documents": [...],
    "discrepancies": [...]
  }},
  "claim_decision": {{
    "status": "approved" | "rejected" | "pending",
    "reason": "short explanation of the decision"
  }}
}}

Respond only with the final decision JSON.
"""
    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[prompt]
    )
    text = response.text or ""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    # Fallback
    return {
        "documents": documents,
        "validation": validation,
        "claim_decision": {
            "status": "rejected",
            "reason": "All required documents present and data is consistent but model failed to evaluate"
        }
    } 