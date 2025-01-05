from models import CardDB
from extensions import db


class CardRepository:
    @staticmethod
    def get_or_create_card(card_rank, card_suit):
        card_from_db = CardDB.query.filter_by(rank=card_rank, suit=card_suit).first()
        if card_from_db is None:
            card_from_db = CardDB(rank=card_rank, suit=card_suit)
            db.session.add(card_from_db)
            db.session.commit()
        return card_from_db




