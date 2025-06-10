import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:0403@localhost:5432/jsd9'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_secret_key')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False


