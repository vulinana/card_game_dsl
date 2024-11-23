from flask import Flask
from src.extensions import socketio, db, migrate
from src.config import Config
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)

socketio.init_app(app)
db.init_app(app)
migrate.init_app(app, db)

with app.app_context():
    from src.models import User
    db.create_all()

from src.gme.routes import gme_routes
app.register_blueprint(gme_routes)

CORS(app)

if __name__ == "__main__":
    print("Flask app instance created:", app)
    socketio.run(app, allow_unsafe_werkzeug=True)
