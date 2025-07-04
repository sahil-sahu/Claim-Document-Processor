import asyncio
import json
import os
import re
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List
from io import BytesIO
import sys
import aiofiles
from google import genai

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.genai import types as gem_types
import httpx
from agents.bill_agent import extract_bill_details
from agents.discharge_agent import extract_discharge_details
from agents.classification_agent import classify_pdfs_with_gemini
from agents.upload_agent import upload_files_to_gemini
from agents.decision_agent import final_decision_agent

# Load environment variables from .env file
load_dotenv()
myconfig = gem_types.UploadFileConfig(mime_type="application/pdf")
app = FastAPI(
    title="PDF Classification and Claim Processing API",
    description="API for uploading, classifying, and processing PDF documents for claims using Gemini.",
    version="1.0.0"
)

# Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Jinja2Templates for HTML responses
templates = Jinja2Templates(directory="templates")

# Configure Gemini API key from environment variable
# The 'google-genai' library automatically picks up GOOGLE_API_KEY.
# Explicit genai.configure() can still be used if you need to override or set it from code.
# However, for consistency with standard library behavior, relying on the env var is good.
# If you explicitly set it here, it will take precedence.

gemini_client = genai.Client()

@app.get("/", response_class=HTMLResponse)

@app.get("/process-claim", response_class=HTMLResponse)
async def get_claim_form(request: Request):
    """
    Serves the HTML form for uploading PDF documents.
    """
    return templates.TemplateResponse("claim_form.html", {"request": request})

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    """
    return {"status": "ok", "message": "API is running"}

@app.post("/process-claim")
async def process_claim(files: List[UploadFile] = File(...)):
    # Step 1: Upload all files to Gemini
    file_resources = await upload_files_to_gemini(gemini_client, files, myconfig)
    # Step 2: Classify all PDFs in a single Gemini call
    classifications = await classify_pdfs_with_gemini(gemini_client, file_resources)
    print(classifications)

    tasks = []
    for item in classifications:
        file_name = item.get("filename")
        doc_type = item.get("type")
        file_resource = file_resources.get(file_name)
        if doc_type == "bill" and file_resource:
            tasks.append(extract_bill_details(gemini_client, file_resource))
        elif doc_type == "discharge_summary" and file_resource:
            tasks.append(extract_discharge_details(gemini_client, file_resource))
        # Add more as needed

    documents = await asyncio.gather(*tasks)

    validation = {
        "missing_documents": [],
        "discrepancies": []
    }
    # Use decision agent to get the final claim decision and full response
    result = final_decision_agent(gemini_client, documents, validation)

    return JSONResponse(content=result) 