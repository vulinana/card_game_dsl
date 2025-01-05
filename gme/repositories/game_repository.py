from sqlalchemy.orm import joinedload

from models import CardDB, UserGameCard, User, GameCard, GameDB, UserGame, PendingCard, GameRequest
from extensions import db


class GameRepository:
    @staticmethod
    def get_user_by_email_and_password(email, password):
        return (
            User.query.filter_by(email=email, password=password).first()
        )
    @staticmethod
    def get_user(email):
        return (
            User.query.filter_by(email=email).first()
        )

    @staticmethod
    def get_user_by_id(id):
        return (
            User.query.filter_by(id=id).first()
        )

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
    def get_table_cards(game_id):
        subquery = db.session.query(CardDB.id, CardDB.rank, CardDB.suit).join(GameCard).filter(GameCard.game_id == game_id).subquery()
        table_cards = db.session.query(subquery).all() #subquery da bi ocuvali duplikate
        table_cards_objects = [CardDB(id=row[0], rank=row[1], suit=row[2]) for row in table_cards]
        return table_cards_objects

    @staticmethod
    def get_or_create_card(card_rank, card_suit):
        card_from_db = CardDB.query.filter_by(rank=card_rank, suit=card_suit).first()
        if card_from_db is None:
            card_from_db = CardDB(rank=card_rank, suit=card_suit)
            db.session.add(card_from_db)
            db.session.commit()
        return card_from_db

    @staticmethod
    def create_table_card(game_id, card_id):
        new_game_card = GameCard(game_id=game_id,
                                 card_id=card_id)
        db.session.add(new_game_card)
        db.session.commit()

    @staticmethod
    def delete_table_card(game_id, card_id):
        table_card_from_db = GameCard.query.filter_by(game_id=game_id, card_id=card_id).first()
        db.session.delete(table_card_from_db)
        db.session.commit()

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
    def create_game_init(name, game_initiator):
        new_game = GameDB(name=name,
                          game_initiator=game_initiator)
        db.session.add(new_game)
        db.session.commit()
        return new_game

    @staticmethod
    def create_game_request(game_id, user_id):
        new_game_request = GameRequest(user_id=user_id, game_id=game_id)
        db.session.add(new_game_request)
        db.session.commit()
        return new_game_request

    @staticmethod
    def get_game(game_id):
        return (
            db.session.query(GameDB)
            .options(
                joinedload(GameDB.current_player),
                joinedload(GameDB.game_requests),
                joinedload(GameDB.game_initiator))
            .filter(GameDB.id == game_id)
            .first()
        )

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
    def update_current_player(game_id, new_current_player_id):
        game = GameDB.query.filter_by(id=game_id).first()
        game.current_player_id = new_current_player_id
        db.session.commit()

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

    @staticmethod
    def increase_game_round(game_id):
        game = GameDB.query.filter_by(id=game_id).first()
        game.current_round = game.current_round + 1
        db.session.commit()

    @staticmethod
    def save_changes():
        db.session.commit()

    @staticmethod
    def update_game_request_status(game_id, user_id, status):
        game_request = GameRequest.query.filter_by(game_id=game_id, user_id=user_id).first()
        game_request.status = status
        db.session.commit()
