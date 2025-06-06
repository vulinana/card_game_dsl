from sqlalchemy.orm import joinedload

from models import GameDB
from extensions import db


class GameRepository:
    @staticmethod
    def create_game_init(name, game_initiator, next_states):
        new_game = GameDB(name=name,
                          game_initiator=game_initiator,
                          next_states=next_states,
                          current_player=game_initiator)
        db.session.add(new_game)
        db.session.commit()
        return new_game

    @staticmethod
    def get_game(game_id):
        return (
            db.session.query(GameDB)
            .options(
                joinedload(GameDB.current_player),
                joinedload(GameDB.game_requests),
                joinedload(GameDB.game_initiator)
            )
            .filter(GameDB.id == game_id)
            .first()
        )

    @staticmethod
    def update_current_player(game_id, new_current_player_id):
        game = GameDB.query.filter_by(id=game_id).first()
        game.current_player_id = new_current_player_id
        db.session.commit()

    @staticmethod
    def update_next_states(game_id, new_next_states):
        game = GameDB.query.filter_by(id=game_id).first()
        game.next_states = new_next_states
        db.session.commit()

    @staticmethod
    def save_changes():
        db.session.commit()

