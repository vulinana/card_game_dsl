from models import CardDB
from extensions import db


class CardRepository:
    @staticmethod
    def create(game_id, rank, suit, score):
        new_card = CardDB(game_id=game_id, rank=rank, suit=suit, score=score)
        db.session.add(new_card)
        db.session.commit()

    @staticmethod
    def get(game_id, rank, suit):
        return CardDB.query.filter_by(game_id=game_id, rank=rank, suit=suit).first()




