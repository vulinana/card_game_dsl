from flask import Flask
from extensions import socketio, db, migrate
from config import Config
from flask_cors import CORS
from gme.routes import gme_routes
import os


app = Flask(__name__)
app.config.from_object(Config)

socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*")
db.init_app(app)
migrate.init_app(app, db)

with app.app_context():
    db.create_all()

app.register_blueprint(gme_routes)

CORS(app)

if __name__ == "__main__":
    print("Flask app instance created:", app)
    port = os.environ.get('PORT', 5000)
    socketio.run(app, host='0.0.0.0', port=port)
