from PIL import Image
from google import generativeai as genai

def summarize_image(file):
    # Load image using PIL
    image = Image.open(file)

    # Configure Gemini client
    genai.configure(api_key="AIzaSyABxxLdOaZodqGhDf1QwwI7DX6-Kxzrzuw")  # Replace with your actual API key

    # Use latest supported multimodal model
    model = genai.GenerativeModel("gemini-2.0-flash")  # or "gemini-1.5-pro"

    # Generate summary
    response = model.generate_content(
        [image, "Summarize the content of this image in a short paragraph."]
    )

    return response.text
