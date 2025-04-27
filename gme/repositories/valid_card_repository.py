from sqlalchemy.orm import joinedload

from models import ValidCard
from extensions import db


class ValidCardRepository:
    @staticmethod
    def create_valid_card(user_id, game_id, card_id, card_type):
        new_valid_card = ValidCard(user_id=user_id,
                                   game_id=game_id,
                                   card_id=card_id,
                                   card_type=card_type)
        db.session.add(new_valid_card)
        db.session.commit()

    @staticmethod
    def get_valid_cards_by_game_id(game_id):
        valid_cards = (
            db.session.query(ValidCard)
            .filter(ValidCard.game_id == game_id)
            .all()
        )
        return valid_cards

    @staticmethod
    def remove_valid_cards(game_id):
        cards = ValidCard.query.filter_by(game_id=game_id).all()
        for card in cards:
            db.session.delete(card)
        db.session.commit()


