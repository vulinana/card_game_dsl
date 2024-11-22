import os

class Config:
    SQLALCHEMY_DATABASE_URI = (
        'mssql+pyodbc://jsd:MaloAzura22@jsd-dbserver.database.windows.net/jsd'
        '?driver=ODBC+Driver+17+for+SQL+Server'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_secret_key')  # Koristite env varijablu za tajni ključ

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False