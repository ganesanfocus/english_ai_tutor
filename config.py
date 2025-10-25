"""
Configuration file for English Practice App - ULTRA OPTIMIZED
"""
import os

PRACTICE_PROMPTS = [
    "What's the most interesting place you've ever visited?",
    "Describe your typical day from morning to evening.",
    "What is your favorite hobby and why do you enjoy it?",
    "Tell me about a memorable experience from your childhood.",
    "What are your goals for the next five years?",
]

GRAMMAR_CORRECTIONS = [
    {'wrong': 'I goed', 'correct': 'I went'},
    {'wrong': 'He don\'t', 'correct': 'He doesn\'t'},
]

# ULTRA STRICT - No fluff, just corrections
AI_SYSTEM_MESSAGE = """You are a grammar checker. Find grammar mistakes and list them.

OUTPUT FORMAT (STRICT):

**Found X mistakes:**

1. ❌ "wrong phrase" → ✅ "correct phrase"
2. ❌ "wrong phrase" → ✅ "correct phrase"

If no mistakes: Say "No grammar mistakes found."

RULES:
- Only list actual grammar mistakes
- Ignore technical terms (AWS, S3, Bedrock, Google)
- Be brief
- No long explanations"""

# ULTRA DIRECT PROMPT
AI_FEEDBACK_PROMPT = """List grammar mistakes in this text:

"{transcript}"

Find:
- Missing "a/an/the"
- Wrong prepositions ("learned something topic" needs "about")
- Wrong verb forms

Technical words (AWS, Bedrock, S3, Google) are CORRECT - ignore them.

Format:
1. ❌ "wrong" → ✅ "correct"
2. ❌ "wrong" → ✅ "correct"

Be brief. Only list mistakes."""

class Config:
    SECRET_KEY = 'dev-secret-key'
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = False
    
    AUDIO_UPLOAD_FOLDER = 'audio_uploads'
    STATIC_FOLDER = 'static'
    AUDIO_FOLDER = os.path.join(STATIC_FOLDER, AUDIO_UPLOAD_FOLDER)
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    MIN_AUDIO_SIZE = 1000
    ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'webm', 'm4a', 'flac'}
    
    WHISPER_MODEL = 'base'
    WHISPER_LANGUAGE = 'en'
    WHISPER_FP16 = False
    
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_SAMPLE_WIDTH = 2
    
    LM_STUDIO_BASE_URL = 'http://localhost:1234'
    LM_STUDIO_TIMEOUT = 30
    LM_STUDIO_TEMPERATURE = 0.1  # Very low = strict
    LM_STUDIO_MAX_TOKENS = 500   # Short responses
    DEFAULT_MODEL = 'deepseek-coder-v2-lite-instruct'
    
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5000']
    
    @staticmethod
    def init_app(app):
        os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}