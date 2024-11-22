from flask import Flask

from .extensions import socketio, db, migrate
from .config import Config
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    socketio.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from .models import User
        db.create_all()

    from .gme.routes import gme_routes
    app.register_blueprint(gme_routes)

    CORS(app)

    return app