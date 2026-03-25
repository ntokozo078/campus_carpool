import os

class Config:
    # Secret key for session management and flash messages
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-campus-key'
    
    # Database configuration
    # Defaulting to SQLite for local development, easily swappable to MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///campus_carpool.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False