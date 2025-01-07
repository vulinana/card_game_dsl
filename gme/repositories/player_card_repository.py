from sqlalchemy.orm import joinedload

from models import CardDB, UserGameCard
from extensions import db


class PlayerCardRepository:
    @staticmethod
    def get_player_cards(game_id, user_id):
        subquery = (
            db.session.query(CardDB.id, CardDB.rank, CardDB.suit)
            .join(UserGameCard, UserGameCard.card_id == CardDB.id)
            .filter(UserGameCard.user_id == user_id, UserGameCard.game_id == game_id)
            .subquery()
        )
        player_cards = db.session.query(subquery).all()  # Koristimo subquery da bismo očuvali duplikate
        player_cards_objects = [CardDB(id=row[0], rank=row[1], suit=row[2]) for row in player_cards]
        return player_cards_objects

    @staticmethod
    def create_player_card(game_id, user_id, card_id):
        new_player_card = UserGameCard(user_id=user_id, game_id=game_id, card_id=card_id)
        db.session.add(new_player_card)
        db.session.commit()

    @staticmethod
    def delete_player_card(user_id, game_id, card_id):
        user_card_from_db = UserGameCard.query.filter_by(user_id=user_id, game_id=game_id,
                                                         card_id=card_id).first()
        db.session.delete(user_card_from_db)
        db.session.commit()

    @staticmethod
    def any_player_has_cards(game_id):
        return db.session.query(db.exists().where(UserGameCard.game_id == game_id)).scalar()

