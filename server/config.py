import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///finadvisor.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }

    # MongoDB (optional — enables MongoDB features alongside SQLite)
    MONGODB_URI = os.environ.get('MONGODB_URI', '')
    MONGODB_DB_NAME = os.environ.get('MONGODB_DB_NAME', 'finadvisor')

    CORS_ORIGINS = os.environ.get('FRONTEND_URL', 'http://localhost:5173')

    # AI Configuration — at least one key enables real LLM responses.
    # Priority: Gemini (free tier) → OpenAI → built-in deterministic fallback.
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', None)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)
    # Legacy field kept for compatibility
    AI_PROVIDER = os.environ.get('AI_PROVIDER', 'builtin')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
