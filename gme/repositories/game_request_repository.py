from models import GameRequest
from extensions import db


class GameRequestRepository:
    @staticmethod
    def create_game_request(game_id, user_id):
        new_game_request = GameRequest(user_id=user_id, game_id=game_id)
        db.session.add(new_game_request)
        db.session.commit()
        return new_game_request

    @staticmethod
    def update_game_request_status(game_id, user_id, status):
        game_request = GameRequest.query.filter_by(game_id=game_id, user_id=user_id).first()
        game_request.status = status
        db.session.commit()
