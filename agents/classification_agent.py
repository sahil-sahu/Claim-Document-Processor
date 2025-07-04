import re
import json
from fastapi import HTTPException

async def classify_pdfs_with_gemini(gemini_client, file_resources: dict) -> list[dict]:
    """
    Classifies PDF documents using the Gemini API via the Files API.
    Returns a list of classification dicts.
    """
    if not file_resources:
        return []

    content_parts = list(file_resources.values())
    filenames = list(file_resources.keys())

    try:
        prompt = (
            "You are a document classifier for medical insurance claims.\n\n"
            "For each PDF document provided, classify it as one of the following types:\n"
            "- 'bill': usually contains billing information, hospital name, itemized charges, or total amount due.\n"
            "- 'discharge_summary': typically includes patient details, diagnosis, admission and discharge dates, and treatment summary.\n"
            "- 'other': if the document does not match any of the above.\n\n"
            f"Here are the filenames I provided: {filenames}.\n\n"
            "Return a JSON array where each element is an object with 'filename' (matching the input) and 'type'.\n"
            "Example output:\n"
            "[{\"filename\": \"file1.pdf\", \"type\": \"bill\"}, {\"filename\": \"file2.pdf\", \"type\": \"id_card\"}]\n\n"
            "Ensure your output includes all filenames. Respond only with the JSON array."
        )
        content_parts.append(prompt)
        response = gemini_client.models.generate_content(model="gemini-1.5-flash", contents=content_parts)
        # print(response.text)
        json_results = []
        try:
            text = response.text or ""
            match = re.search(r'\[.*\]', text.strip(), re.DOTALL)
            if match:
                json_string = match.group(0)
                json_results = json.loads(json_string)
            else:
                print(f"Warning: No JSON array found in Gemini response: {response.text}")
                json_results = [{"filename": fname, "type": "other", "reason": "No JSON found in response"} for fname in filenames]

            final_classifications = []
            for fname in filenames:
                found = False
                for item in json_results:
                    if item.get("filename") == fname:
                        final_classifications.append(item)
                        found = True
                        break
                if not found:
                    final_classifications.append({"filename": fname, "type": "other", "reason": "Filename not found in model's JSON output"})
            return final_classifications
        except json.JSONDecodeError as e:
            print(f"Gemini response JSON decoding error: {e}, Response text: {response.text}")
            return [{"filename": fname, "type": "other", "reason": f"Invalid JSON response: {e}"} for fname in filenames]
        except Exception as e:
            print(f"Error processing Gemini response: {e}, Response text: {response.text}")
            return [{"filename": fname, "type": "other", "reason": f"Error processing response: {e}"} for fname in filenames]
    except Exception as e:
        print(f"An unexpected error occurred during classification: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error during PDF classification: {e}") 