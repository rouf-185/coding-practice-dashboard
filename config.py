"""
Application configuration.
"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(16))
    
    # Database
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(INSTANCE_DIR, "codingflashcard.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4MB
    AVATAR_UPLOAD_DIR = os.path.join(BASE_DIR, 'static', 'uploads', 'avatars')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Brevo (email service)
    BREVO_API_KEY = os.getenv('BREVO_API_KEY', '')
    BREVO_FROM_EMAIL = os.getenv('BREVO_FROM_EMAIL', 'info@jobdistributor.net')
    BREVO_FROM_NAME = os.getenv('BREVO_FROM_NAME', 'CodingFlashcard')
    
    # URLs
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5000')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Export the active config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get the active configuration based on environment."""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
