import os

class Config:
    SQLALCHEMY_DATABASE_URI = (
        'postgresql://card_game_jsd_user:SO055pW1rNdyN32MRdsrsjQdp1ZnKFaV@dpg-cu184nhu0jms738gnoq0-a.frankfurt-postgres.render.com/card_game_jsd'
    )
    #SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:0403@localhost:5432/jsd14'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_secret_key')  # Koristite env varijablu za tajni ključ

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False