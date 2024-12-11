import os

class Config:
    #SQLALCHEMY_DATABASE_URI = (
    #    'postgresql://postgres:myhNAiNTJAltMmxjBOFatbshqNSChyyI@autorack.proxy.rlwy.net:23481/railway'
    #)
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:0403@localhost:5432/jsd2'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_secret_key')  # Koristite env varijablu za tajni ključ

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False