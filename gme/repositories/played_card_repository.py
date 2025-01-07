from sqlalchemy.orm import joinedload

from models import PlayedCard, Round
from extensions import db


class PlayedCardRepository:
    @staticmethod
    def create_played_card(user_id, game_id, card_id, round_id):
        new_played_card = PlayedCard(user_id=user_id,
                                   game_id=game_id,
                                   card_id=card_id,
                                   round_id=round_id)
        db.session.add(new_played_card)
        db.session.commit()

    @staticmethod
    def get_played_cards_by_game_id_and_round_id(game_id, round_id):
        played_cards = (
            db.session.query(PlayedCard)
            .join(Round, PlayedCard.round_id == Round.id)
            .filter(PlayedCard.game_id == game_id, PlayedCard.round_id == round_id)
            .options(joinedload(PlayedCard.card))
            .all()
        )
        return played_cards


