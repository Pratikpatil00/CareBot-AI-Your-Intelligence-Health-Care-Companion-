import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
# Exactly one explicit dotenv location, independent of the working directory.
load_dotenv(ROOT / '.env')

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///' + (ROOT / 'data/carebot.db').as_posix()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', '')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    JWT_TOKEN_LOCATION = ['cookies']
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_COOKIE_SECURE = os.getenv('COOKIE_SECURE', 'false').lower() == 'true'
    JWT_COOKIE_SAMESITE = 'Lax'
    JWT_SESSION_COOKIE = True
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    MAX_FORM_MEMORY_SIZE = 100_000
    MAX_FORM_PARTS = 20
    UPLOAD_ROOT = ROOT / 'data/uploads'
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = os.getenv('GROQ_MODEL') or 'openai/gpt-oss-20b'
    GROQ_VISION_MODEL = os.getenv('GROQ_VISION_MODEL') or 'qwen/qwen3.8-27b'
    MAPPLS_API_KEY = os.getenv('MAPPLS_API_KEY', '')
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', '')
    RATELIMIT_STORAGE_URI = os.getenv('RATE_LIMIT_STORAGE_URI') or 'memory://'
