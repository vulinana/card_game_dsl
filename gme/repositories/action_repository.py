from models import CardDB, GameAction
from extensions import db


class ActionRepository:
    @staticmethod
    def create(game_id, action_type):
        new_action = GameAction(game_id=game_id, action_type=action_type)
        db.session.add(new_action)
        db.session.commit()

    @staticmethod
    def get_by_game_id(game_id):
        return GameAction.query.filter_by(game_id=game_id).first()

