import google.generativeai as genai
import tempfile
import shutil
import os
import mimetypes

# Configure API
genai.configure(api_key="AIzaSyABxxLdOaZodqGhDf1QwwI7DX6-Kxzrzuw")
model = genai.GenerativeModel("gemini-1.5-pro")

def summarize_audio(file) -> str:
    original_name = getattr(file, 'name', '')
    extension = os.path.splitext(original_name)[1] or ".mp3"

    # Save file temporarily
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
        shutil.copyfileobj(file, temp_file)
        temp_file_path = temp_file.name

    # Check MIME type
    mime_type, _ = mimetypes.guess_type(temp_file_path)
    if not mime_type:
        os.remove(temp_file_path)
        raise ValueError("Could not determine MIME type for the uploaded audio file.")

    # Transcribe audio using Gemini (text prompt approach)
    response = model.generate_content([
        "Please describe the following audio file in detail:",
        {"mime_type": mime_type, "data": open(temp_file_path, "rb").read()}
    ])

    os.remove(temp_file_path)
    return response.text.strip()
