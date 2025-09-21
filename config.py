#!/usr/bin/env python3
"""
Configuration file for English Practice App
Contains all configuration settings and constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    
    # Server configuration
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
    
    # Directory configuration
    BASE_DIR = Path(__file__).parent
    STATIC_FOLDER = 'static'
    TEMPLATE_FOLDER = 'templates'
    AUDIO_UPLOAD_FOLDER = 'audio_uploads'
    
    # Whisper configuration
    WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # base, small, medium, large
    WHISPER_LANGUAGE = 'en'
    WHISPER_FP16 = False
    
    # Audio processing configuration
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHANNELS = 1
    AUDIO_SAMPLE_WIDTH = 2
    MIN_AUDIO_SIZE = 1000  # bytes
    
    # LM Studio configuration
    LM_STUDIO_BASE_URL = os.getenv('LM_STUDIO_URL', 'http://localhost:1234')
    LM_STUDIO_TIMEOUT = 30  # seconds
    LM_STUDIO_MAX_TOKENS = 500
    LM_STUDIO_TEMPERATURE = 0.7
    
    # Default AI model
    DEFAULT_MODEL = 'llama-3.2-3b-instruct'
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'app.log')
    
    @property
    def audio_folder_path(self):
        """Get the full path to audio upload folder"""
        return os.path.join(self.BASE_DIR, self.STATIC_FOLDER, self.AUDIO_UPLOAD_FOLDER)
    
    @classmethod
    def init_app(cls, app):
        """Initialize app with configuration"""
        # Set the audio folder path in app config
        audio_path = os.path.join(cls.BASE_DIR, cls.STATIC_FOLDER, cls.AUDIO_UPLOAD_FOLDER)
        app.config['AUDIO_FOLDER'] = audio_path
        
        # Create necessary directories
        os.makedirs(audio_path, exist_ok=True)
        print(f"Audio upload folder: {audio_path}")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    HOST = '0.0.0.0'
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    HOST = '127.0.0.1'
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Production CORS - restrict origins
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        
        # Ensure secret key is set in production
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable must be set in production")

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    WHISPER_MODEL = 'tiny'  # Use smallest model for faster tests
    
# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Practice prompts for the application
PRACTICE_PROMPTS = [
    "Tell me about your favorite hobby and why you enjoy it.",
    "Describe your typical day from morning to evening.",
    "What's the most interesting place you've ever visited?",
    "Explain how to make your favorite dish.",
    "What are your goals for the next five years?",
    "Describe someone who has influenced your life.",
    "What's your opinion about social media and its impact?",
    "Tell me about a book or movie that changed your perspective.",
    "How do you handle stressful situations in your life?",
    "What would you do if you won a million dollars?",
    "Describe your dream job and why it appeals to you.",
    "What's the biggest challenge you've overcome?",
    "How has technology changed our daily lives?",
    "What advice would you give to your younger self?",
    "Describe a memorable experience from your childhood.",
    "What does success mean to you?",
    "How do you maintain work-life balance?",
    "What skills would you like to learn and why?",
    "Describe your ideal vacation destination.",
    "What motivates you to keep learning new things?"
]

# Basic grammar rules for fallback analysis
GRAMMAR_CORRECTIONS = [
    {"wrong": "have completed", "correct": "completed"},
    {"wrong": "in Coimbatore KIT College", "correct": "at KIT College in Coimbatore"},
    {"wrong": "in 2019 from January 1st", "correct": "on January 1, 2019"},
    {"wrong": "a fresh air", "correct": "a fresher"},
    {"wrong": "100 application development", "correct": "Android application development"},
    {"wrong": "under 6 months course", "correct": "a six-month course"},
    {"wrong": "we started in my company they changed their language", "correct": "my company changed its primary language"},
    {"wrong": "Python Floss", "correct": "Python Flask"},
    {"wrong": "landed in", "correct": "transitioned to"},
    {"wrong": "I promoted to", "correct": "I was promoted to"},
    {"wrong": "had 4 team members", "correct": "had a team of 4 members"},
    {"wrong": "I have completed", "correct": "I completed"},
    {"wrong": "I am working in", "correct": "I work at"},
    {"wrong": "I am doing job", "correct": "I work"},
    {"wrong": "good marks", "correct": "good grades"},
    {"wrong": "give exam", "correct": "take an exam"},
    {"wrong": "passed out", "correct": "graduated"},
    {"wrong": "doing masters", "correct": "pursuing a master's degree"},
    {"wrong": "marriage function", "correct": "wedding ceremony"},
    {"wrong": "I have doubt", "correct": "I have a question"}
]

# AI prompt templates
AI_FEEDBACK_PROMPT = """You are an English language teacher helping a student improve their speaking skills. 
Please analyze this transcript and provide helpful feedback:
"{transcript}"

Focus on:
1. Grammar mistakes and corrections
2. Word choice improvements  
3. Sentence structure suggestions
4. Pronunciation tips (if obvious from text)
5. Overall communication effectiveness

Be encouraging but specific about improvements. Format your response clearly with numbered points."""

AI_SYSTEM_MESSAGE = "You are a helpful and expert English language teacher."