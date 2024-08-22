# ./frontend/config.py
import os

import os

class Config:
    # Base configuration
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'Super Ultra Mega Secret')
    CSRF_SESSION_KEY = os.getenv('CSRF_SESSION_KEY', 'Super Ultra Mega Secret')
    THREADS_PER_PAGE = 2
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', 'glpat-E_kgHVP33iy5T-DmaGDT')
    BASE_BACKEND_URL = os.getenv('BASE_BACKEND_URL', 'http://localhost:8000')  # Default to localhost
    PORT = os.getenv('PORT', 5000)  # Default port

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True

