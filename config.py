import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'edu-mgmt-secret-key-2024-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'education.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB upload limit
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    SCHOOL_NAME = os.environ.get('SCHOOL_NAME', 'EduManage Pro')
    SCHOOL_ADDRESS = os.environ.get('SCHOOL_ADDRESS', '123 Education Avenue, Knowledge City')
    SCHOOL_PHONE = os.environ.get('SCHOOL_PHONE', '+1-555-0100')
    SCHOOL_EMAIL = os.environ.get('SCHOOL_EMAIL', 'info@edumanagepro.com')
    ACADEMIC_YEAR = os.environ.get('ACADEMIC_YEAR', '2024-2025')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
