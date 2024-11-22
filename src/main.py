from src import create_app
from src.extensions import socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app)