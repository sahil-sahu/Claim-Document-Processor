from io import BytesIO
from fastapi import UploadFile

async def upload_files_to_gemini(gemini_client, files: list, myconfig) -> dict:
    """
    Uploads files to Gemini and returns a dict mapping filename to file resource.
    """
    file_resources = {}
    for _file in files:
        file_bytes = await _file.read()
        file_stream = BytesIO(file_bytes)
        uploaded_file = gemini_client.files.upload(file=file_stream, config=myconfig)
        file_resources[_file.filename] = uploaded_file
        print(f"Uploaded {_file.filename} to Gemini Files API with URI: {uploaded_file.uri}")
    return file_resources 