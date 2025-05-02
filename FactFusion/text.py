from google import genai
from docx import Document
from io import BytesIO
import PyPDF2
import textract
import os
import tempfile

def summarize_text(file) -> str:
    file_name = file.name
    file_extension = os.path.splitext(file_name)[1].lower()

    text_content = ""

    try:
        if file_extension == ".txt":
            text_content = file.read().decode("utf-8", errors="ignore")

        elif file_extension == ".docx":
            doc = Document(BytesIO(file.read()))
            text_content = "\n".join(para.text for para in doc.paragraphs)

        elif file_extension == ".pdf":
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text_content += page.extract_text() or ""

        elif file_extension == ".rtf":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".rtf") as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            text_content = textract.process(tmp_path).decode("utf-8")
            os.remove(tmp_path)

        else:
            # Generic fallback with textract for other supported types
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
                tmp.write(file.read())
                tmp_path = tmp.name
            text_content = textract.process(tmp_path).decode("utf-8")
            os.remove(tmp_path)

    except Exception as e:
        return f"❌ Error reading file: {e}"

    if not text_content.strip():
        return "⚠️ No readable text found in the document."

    try:
        # Initialize Gemini client
        client = genai.Client(api_key="AIzaSyABxxLdOaZodqGhDf1QwwI7DX6-Kxzrzuw")

        # Trim long content if needed (Gemini Flash supports ~30k tokens)
        if len(text_content) > 30000:
            text_content = text_content[:30000]

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=["Summarize this text: " + text_content]
        )

        return response.text.strip()

    except Exception as e:
        return f"❌ Error with Gemini API: {e}"
