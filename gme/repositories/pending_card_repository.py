from sqlalchemy.orm import joinedload

from models import PendingCard
from extensions import db


class PendingCardRepository:
    @staticmethod
    def create_pending_card(game_id, card_id, count):
        new_pending_card = PendingCard(game_id=game_id,
                                 card_id=card_id, count=count)
        db.session.add(new_pending_card)
        db.session.commit()

    @staticmethod
    def get_game_pending_cards(game_id):
        return (
            db.session.query(PendingCard)
            .options(joinedload(PendingCard.card))
            .filter(PendingCard.game_id == game_id)
            .all()
        )

    @staticmethod
    def remove_pending_card(game_id, card_id):
        pending_card = PendingCard.query.filter_by(game_id=game_id, card_id=card_id).first()
        if pending_card.count > 1:
            pending_card.count = pending_card.count - 1
        else:
            db.session.delete(pending_card)
        db.session.commit()

