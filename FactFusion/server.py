from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from rag_pipeline import configure, fact_check
import audio
import video
import text
import images

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure RAG pipeline
if not configure():
    print("Warning: Failed to configure RAG pipeline")

def get_file_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
        return 'audio'
    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv']:
        return 'video'
    elif ext in ['.txt', '.doc', '.docx', '.pdf', '.rtf']:
        return 'text'
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']:
        return 'images'
    return None

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/process', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save file temporarily
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Get file type and process accordingly
        file_type = get_file_type(filename)
        if not file_type:
            return jsonify({'error': 'Unsupported file type'}), 400

        # Generate summary based on file type
        summary = ""
        if file_type == 'audio':
            summary = audio.summarize_audio(filepath)
        elif file_type == 'video':
            summary = video.summarize_video(filepath)
        elif file_type == 'text':
            summary = text.summarize_text(filepath)
        elif file_type == 'images':
            summary = images.summarize_image(filepath)

        if not summary:
            return jsonify({'error': 'Failed to generate summary'}), 500

        # Perform fact-checking
        fact_check_result = fact_check(summary)

        # Clean up temporary file
        os.remove(filepath)

        return jsonify({
            'summary': summary,
            'factCheck': {
                'trust_score': fact_check_result.trust_score,
                'explanation': fact_check_result.explanation,
                'supporting_points': fact_check_result.supporting_points,
                'contradictory_points': fact_check_result.contradictory_points,
                'raw_evidence': fact_check_result.raw_evidence
            }
        })

    except Exception as e:
        # Clean up temporary file in case of error
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True) 