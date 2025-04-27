from models import CardDB, UserGameCard
from extensions import db


class PlayerCardRepository:
    @staticmethod
    def get_player_cards(game_id, user_id):
        player_cards = (
            db.session.query(UserGameCard)
            .join(CardDB, UserGameCard.card)
            .filter(UserGameCard.game_id == game_id, UserGameCard.user_id == user_id)
            .order_by(UserGameCard.id)
            .all()
        )
        return player_cards

    @staticmethod
    def get(id):
        return db.session.query(UserGameCard).join(CardDB, UserGameCard.card).filter(UserGameCard.id == id).first()

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
    def delete_player_card_by_id(id):
        user_card_from_db = UserGameCard.query.filter_by(id=id).first()
        db.session.delete(user_card_from_db)
        db.session.commit()

    @staticmethod
    def delete_players_cards(game_id):
        cards = UserGameCard.query.filter_by(game_id=game_id)
        for card in cards:
            db.session.delete(card)
        db.session.commit()

    @staticmethod
    def any_player_has_cards(game_id):
        return db.session.query(db.exists().where(UserGameCard.game_id == game_id)).scalar()

