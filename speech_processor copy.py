#!/usr/bin/env python3
"""
Backend server for English Practice App
Flask backend with Whisper transcription using external configuration
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import whisper
import os
import uuid
import numpy as np
import soundfile as sf
import random
from datetime import datetime
from pydub import AudioSegment
from werkzeug.utils import secure_filename
import requests

# Import configuration
from config import config, PRACTICE_PROMPTS, GRAMMAR_CORRECTIONS, AI_FEEDBACK_PROMPT, AI_SYSTEM_MESSAGE

# Global variables
model = None

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    app = Flask(__name__, 
                static_folder='static', 
                static_url_path='/static',
                template_folder='templates')
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Setup CORS
    if config_name == 'production':
        CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})
    else:
        CORS(app)
    
    # Load Whisper model
    global model
    if model is None:
        print(f"Loading Whisper model: {app.config['WHISPER_MODEL']}...")
        model = whisper.load_model(app.config['WHISPER_MODEL'])
        print("Whisper model loaded successfully!")
    
    # Helper functions
    def allowed_file(filename):
        """Check if the file has an allowed extension."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    def convert_to_wav_compatible(input_path: str) -> str:
        """Convert any audio file to mono 16kHz PCM WAV compatible with Whisper."""
        try:
            sound = AudioSegment.from_file(input_path)
            sound = sound.set_frame_rate(app.config['AUDIO_SAMPLE_RATE']) \
                        .set_channels(app.config['AUDIO_CHANNELS']) \
                        .set_sample_width(app.config['AUDIO_SAMPLE_WIDTH'])
            
            base_name = os.path.splitext(os.path.basename(input_path))[0]
            output_filename = f"{base_name}_fixed.wav"
            output_path = os.path.join(app.config['AUDIO_FOLDER'], output_filename)
            
            sound.export(output_path, format="wav")
            print(f"Converted to compatible WAV: {output_path}")
            return output_path
        except Exception as e:
            raise RuntimeError(f"Audio conversion failed: {e}")

    def normalize_audio(audio_path: str):
        """Normalize audio volume so Whisper can transcribe low-volume recordings."""
        try:
            data, samplerate = sf.read(audio_path)
            if len(data.shape) > 1:  # stereo -> mono
                data = np.mean(data, axis=1)
            max_abs = np.max(np.abs(data))
            if max_abs > 0:
                data = data / max_abs  # normalize volume
                sf.write(audio_path, data, samplerate)
                print(f"Audio normalized: {audio_path}")
        except Exception as e:
            print(f"Normalization warning: {e}")

    def analyze_basic_grammar(transcript):
        """Fallback grammar analysis when LM Studio isn't available"""
        feedback = "### Basic Grammar Feedback:\n\n"
        found_mistakes = 0

        for mistake in GRAMMAR_CORRECTIONS:
            if mistake['wrong'] in transcript:
                found_mistakes += 1
                feedback += f"{found_mistakes}. **Correction:** \"{mistake['wrong']}\" should be \"{mistake['correct']}\".\n"

        if found_mistakes == 0:
            feedback = "Great job! I didn't detect any of these common grammar mistakes. Keep practicing!"
        else:
            feedback += f"\n**Keep up the great work!** Focusing on these {found_mistakes} points will make your English even more fluent."

        return feedback

    # Routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'whisper_model': app.config['WHISPER_MODEL'],
            'static_folder': app.static_folder,
            'audio_folder': app.config['AUDIO_FOLDER'],
            'folder_exists': os.path.exists(app.config['AUDIO_FOLDER']),
            'config': config_name
        })

    @app.route('/models', methods=['GET'])
    def get_available_models():
        """Get available models from LM Studio"""
        try:
            response = requests.get(
                f"{app.config['LM_STUDIO_BASE_URL']}/v1/models", 
                timeout=app.config['LM_STUDIO_TIMEOUT']
            )
            if response.ok:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'LM Studio not available'}), 503
        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Cannot connect to LM Studio: {str(e)}'}), 503

    @app.route('/prompts', methods=['GET'])
    def get_random_prompt():
        """Get a random practice prompt"""
        return jsonify({
            'prompt': random.choice(PRACTICE_PROMPTS),
            'total_prompts': len(PRACTICE_PROMPTS)
        })

    @app.route('/transcribe', methods=['POST'])
    def transcribe_audio():
        original_audio_path = None
        fixed_audio_path = None
        try:
            if 'audio' not in request.files:
                return jsonify({'error': 'No audio file provided'}), 400

            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            if not allowed_file(audio_file.filename):
                return jsonify({'error': 'File type not allowed'}), 400

            # Generate secure filename
            safe_filename = secure_filename(audio_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            final_filename = f"audio_{timestamp}_{unique_id}_{safe_filename}"
            
            original_audio_path = os.path.join(app.config['AUDIO_FOLDER'], final_filename)
            
            # Check file size
            audio_file.seek(0, 2)
            file_size = audio_file.tell()
            audio_file.seek(0)
            
            if file_size > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': 'File too large'}), 413
            
            if file_size < app.config['MIN_AUDIO_SIZE']:
                return jsonify({'error': 'File too small or empty'}), 400

            # Save and process file
            audio_file.save(original_audio_path)
            print(f"File saved successfully: {original_audio_path} (size: {file_size} bytes)")

            fixed_audio_path = convert_to_wav_compatible(original_audio_path)
            normalize_audio(fixed_audio_path)

            # Transcribe with Whisper
            print("Starting Whisper transcription...")
            result = model.transcribe(
                fixed_audio_path, 
                fp16=app.config['WHISPER_FP16'], 
                language=app.config['WHISPER_LANGUAGE']
            )
            transcript = result['text'].strip()
            print(f"Transcription: '{transcript}'")

            return jsonify({
                'transcript': transcript,
                'language': app.config['WHISPER_LANGUAGE'],
                'success': True,
                'file_size': file_size,
                'filename': final_filename,
                'static_path': f"static/{app.config['AUDIO_UPLOAD_FOLDER']}/{os.path.basename(fixed_audio_path)}"
            })

        except Exception as e:
            print(f"Error during transcription: {e}")
            return jsonify({
                'error': f'Transcription failed: {str(e)}',
                'success': False
            }), 500
        finally:
            # Cleanup temporary files
            if original_audio_path and os.path.exists(original_audio_path):
                os.remove(original_audio_path)
            if fixed_audio_path and os.path.exists(fixed_audio_path):
                os.remove(fixed_audio_path)

    @app.route('/analyze', methods=['POST'])
    def analyze_speech():
        """Analyze speech with LM Studio or fallback to basic analysis"""
        try:
            data = request.get_json()
            if not data or 'transcript' not in data:
                return jsonify({'error': 'No transcript provided'}), 400

            transcript = data['transcript']

            # Try LM Studio first
            try:
                prompt = AI_FEEDBACK_PROMPT.format(transcript=transcript)
                
                response = requests.post(
                    f"{app.config['LM_STUDIO_BASE_URL']}/v1/chat/completions",
                    json={
                        "model": app.config['DEFAULT_MODEL'],
                        "messages": [
                            {"role": "system", "content": AI_SYSTEM_MESSAGE},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": app.config['LM_STUDIO_TEMPERATURE'],
                        "max_tokens": app.config['LM_STUDIO_MAX_TOKENS']
                    },
                    timeout=app.config['LM_STUDIO_TIMEOUT']
                )

                if response.ok:
                    result = response.json()
                    ai_feedback = result['choices'][0]['message']['content']
                    return jsonify({
                        'feedback': ai_feedback,
                        'source': 'ai',
                        'success': True
                    })
                else:
                    raise requests.RequestException("LM Studio request failed")

            except requests.RequestException:
                # Fallback to basic analysis
                basic_feedback = analyze_basic_grammar(transcript)
                return jsonify({
                    'feedback': basic_feedback,
                    'source': 'basic',
                    'success': True
                })

        except Exception as e:
            print(f"Error during analysis: {e}")
            return jsonify({
                'error': f'Analysis failed: {str(e)}',
                'success': False
            }), 500

    return app

# For running directly
if __name__ == '__main__':
    app = create_app()
    
    print("Starting English Practice Backend Server...")
    print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"Whisper model: {app.config['WHISPER_MODEL']}")
    print(f"Audio storage: {app.config['AUDIO_FOLDER']}")
    print(f"Server running on http://{app.config['HOST']}:{app.config['PORT']}")
    print("\nEndpoints:")
    print("   GET  /             - Main application")
    print("   GET  /health       - Health check")
    print("   GET  /models       - Get LM Studio models")
    print("   GET  /prompts      - Get random prompt")
    print("   POST /transcribe   - Process audio file")
    print("   POST /analyze      - Analyze transcript")
    
    app.run(
        host=app.config['HOST'], 
        port=app.config['PORT'], 
        debug=app.config['DEBUG']
    )