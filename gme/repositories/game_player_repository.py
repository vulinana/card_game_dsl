from sqlalchemy.orm import joinedload

from models import UserGame
from extensions import db


class GamePlayerRepository:
    @staticmethod
    def create_game_player(game_id, user_id):
        new_user_game = UserGame(user_id=user_id, game_id=game_id, points=0)
        db.session.add(new_user_game)
        db.session.commit()
        return new_user_game

    @staticmethod
    def get_game_players(game_id):
        return (
            db.session.query(UserGame).filter_by(game_id=game_id)
            .options(joinedload(UserGame.user))
            .all()
        )

    @staticmethod
    def get_game_player(game_id, user_id):
        return UserGame.query.filter_by(game_id=game_id, user_id=user_id).first()

    @staticmethod
    def update_player_points(user_id, game_id, points):
        game_player = GamePlayerRepository.get_game_player(game_id, user_id)
        game_player.points += points
        db.session.commit()

