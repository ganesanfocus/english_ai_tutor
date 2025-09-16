#!/usr/bin/env python3
"""
Backend server for English Practice App
Flask backend with Whisper transcription (English only, with audio normalization and auto audio conversion).
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import whisper
import os
import time
import uuid
import numpy as np
import soundfile as sf
from datetime import datetime
from pydub import AudioSegment

app = Flask(__name__)
CORS(app)

# Use static folder for audio files
AUDIO_FOLDER = os.path.join(app.static_folder, 'audio_uploads')
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)
    print(f"Created directory: {AUDIO_FOLDER}")

# Load Whisper model once at startup
print("Loading Whisper model...")
model = whisper.load_model("base")  # change to "small" / "medium" if needed
print("Whisper model loaded successfully!")

def convert_to_wav_compatible(input_path: str) -> str:
    """Convert any audio file to mono 16kHz PCM WAV compatible with Whisper."""
    try:
        sound = AudioSegment.from_file(input_path)
        sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        # Fix: Create a new output path with a .wav extension
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}_fixed.wav")
        
        sound.export(output_path, format="wav")
        print(f"Converted to compatible WAV: {output_path}")
        return output_path
    except Exception as e:
        raise RuntimeError(f"Audio conversion failed: {e}")

def normalize_audio(audio_path: str):
    """Normalize audio volume so Whisper can transcribe low-volume recordings."""
    try:
        data, samplerate = sf.read(audio_path)
        if len(data.shape) > 1:  # stereo → mono
            data = np.mean(data, axis=1)
        max_abs = np.max(np.abs(data))
        if max_abs > 0:
            data = data / max_abs  # normalize volume
            sf.write(audio_path, data, samplerate)
            print(f"Audio normalized: {audio_path}")
    except Exception as e:
        print(f"Normalization warning: {e}")

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    audio_path = None
    fixed_path = None
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Generate unique filename with original extension
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        # Use the original file extension to save the file correctly
        original_extension = os.path.splitext(audio_file.filename)[1]
        filename = f"audio_{timestamp}_{unique_id}{original_extension}"

        # Save file to static/audio_uploads
        audio_path = os.path.join(AUDIO_FOLDER, filename)
        print(f"Saving audio to static folder: {audio_path}")

        audio_data = audio_file.read()
        print(f"Read {len(audio_data)} bytes from uploaded file")

        with open(audio_path, 'wb') as f:
            f.write(audio_data)
            f.flush()
            os.fsync(f.fileno())

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"File not saved: {audio_path}")

        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            raise ValueError("Audio file is empty")
        if file_size < 1000:
            return jsonify({'error': 'Audio file too short'}), 400

        print(f"File saved successfully: {audio_path} (size: {file_size} bytes)")

        # Small delay to ensure file I/O is finished
        time.sleep(0.2)

        # Convert to Whisper-compatible WAV
        fixed_path = convert_to_wav_compatible(audio_path)

        # Normalize audio
        normalize_audio(fixed_path)

        # Transcribe
        print("Starting Whisper transcription (English only)...")
        result = model.transcribe(fixed_path, fp16=False, language="en")

        transcript = result['text'].strip()
        print(f"Transcription: '{transcript}'")

        return jsonify({
            'transcript': transcript,
            'language': "en",
            'success': True,
            'file_size': file_size,
            'filename': filename,
            'static_path': f"static/audio_uploads/{filename}"
        })

    except Exception as e:
        print(f"Error during transcription: {e}")
        return jsonify({
            'error': f'Transcription failed: {str(e)}',
            'success': False
        }), 500

# Cleanup section has been removed from here.

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'whisper_model': 'base',
        'static_folder': app.static_folder,
        'audio_folder': AUDIO_FOLDER,
        'folder_exists': os.path.exists(AUDIO_FOLDER)
    })

@app.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """Clean up leftover audio files"""
    try:
        if not os.path.exists(AUDIO_FOLDER):
            return jsonify({'message': 'No audio folder found'})

        files = os.listdir(AUDIO_FOLDER)
        deleted_count = 0

        for file in files:
            if file.startswith('audio_') and file.endswith(('.wav', '.mp3', '.m4a', '.ogg')):
                file_path = os.path.join(AUDIO_FOLDER, file)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"Could not delete {file}: {e}")

        return jsonify({
            'message': 'Cleanup complete',
            'files_deleted': deleted_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting English Practice Backend Server...")
    print("Whisper model: base (CPU mode, English only, with normalization and auto conversion)")
    print(f"Static folder: {app.static_folder}")
    print(f"Audio storage: {AUDIO_FOLDER}")
    print("Server running on http://localhost:5000")
    print("\nEndpoints:")
    print("  GET  /              - Main application (renders template)")
    print("  GET  /health        - Health check")
    print("  POST /transcribe    - Process audio file")
    print("  POST /cleanup       - Clean up old audio files")

    app.run(host='0.0.0.0', port=5000, debug=True)