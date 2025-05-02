import os
import cv2
import shutil
from datetime import timedelta
from deep_translator import GoogleTranslator
from difflib import SequenceMatcher
from typing import List
from faster_whisper import WhisperModel
import easyocr
import google.generativeai as genai
import time

# Temporary directory for intermediate artifacts
TEMP_DIR = "temp_summary_data"

# ----------------- FRAME EXTRACTION -----------------
def extract_frames(video_path: str, output_dir: str, interval_sec: int = 2) -> List[str]:
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * interval_sec)
    count = 0
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if count % interval == 0:
            timestamp = str(timedelta(seconds=int(cap.get(cv2.CAP_PROP_POS_MSEC)/1000)))
            path = os.path.join(output_dir, f"frame_{timestamp.replace(':', '-')}.jpg")
            cv2.imwrite(path, frame)
            frames.append(path)
        count += 1
    cap.release()
    return frames

# ----------------- OCR & TRANSLATION -----------------
def clean_text(text: str) -> str:
    text = text.strip()
    return text if len(text) >= 3 else ""

def translate_text(text: str) -> str:
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception:
        return text  # fallback if translation fails

def deduplicate_text(texts: List[str], threshold=0.8) -> List[str]:
    unique = []
    for text in texts:
        if all(SequenceMatcher(None, text, u).ratio() < threshold for u in unique):
            unique.append(text)
    return unique

def extract_and_translate_text_from_frames(frames: List[str], reader) -> List[str]:
    all_text = []
    for frame_path in frames:
        lines = reader.readtext(frame_path, detail=0)
        for line in lines:
            cleaned = clean_text(line)
            if cleaned:
                translated = translate_text(cleaned)
                all_text.append(translated)
    return deduplicate_text(all_text)

# ----------------- GEMINI SETUP -----------------
genai.configure(api_key="AIzaSyABxxLdOaZodqGhDf1QwwI7DX6-Kxzrzuw")
gemini_model = genai.GenerativeModel("gemini-2.0-flash")

# ----------------- AUDIO TRANSCRIPTION (WHISPER ONLY) -----------------
def transcribe_audio_with_whisper(video_path: str) -> str:
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path)
    return " ".join([seg.text for seg in segments])

# ----------------- GEMINI SUMMARY -----------------
def generate_final_summary(spoken: str, visual: List[str]) -> str:
    visual_str = ". ".join(visual)
    prompt = (
        f"Given the following spoken transcript and visual text extracted from a video, generate a concise and coherent "
        f"English summary that meaningfully fuses both sources without including irrelevant details.\n\n"
        f"SPOKEN:\n{spoken}\n\n"
        f"VISUAL TEXT:\n{visual_str}\n\n"
        f"SUMMARY:"
    )
    response = gemini_model.generate_content(prompt)
    return response.text.strip()

# ----------------- FULL MULTIMODAL SUMMARY PROCESS -----------------
def summarize_video(file) -> str:
    import mimetypes

    use_gpu = True
    print(f"[⚙] Running with GPU: {use_gpu}")

    # Create temp directory
    os.makedirs(TEMP_DIR, exist_ok=True)

    # Infer the extension (fallback to .mp4 if unknown)
    mime_type, _ = mimetypes.guess_type(file.name)
    ext = mimetypes.guess_extension(mime_type) or ".mp4"

    # Save uploaded video file
    video_temp_path = os.path.join(TEMP_DIR, f"uploaded_video{ext}")
    with open(video_temp_path, "wb") as f_out:
        f_out.write(file.read())

    frames_dir = os.path.join(TEMP_DIR, "frames")
    reader = easyocr.Reader(['en'], gpu=use_gpu)

    print("[🔄] Extracting frames...")
    frames = extract_frames(video_temp_path, frames_dir)

    print("[🔊] Transcribing audio with Whisper...")
    spoken_text = transcribe_audio_with_whisper(video_temp_path)

    print("[🌍] OCR and translating visual text...")
    visual_texts = extract_and_translate_text_from_frames(frames, reader)

    print("[📝] Generating final summary using Gemini...")
    summary = generate_final_summary(spoken_text, visual_texts)

    print("[🧹] Cleaning up temporary files...")
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    return summary



