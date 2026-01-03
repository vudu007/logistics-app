import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-super-secret'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trucks.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False