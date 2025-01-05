from models import CardDB, GameCard
from extensions import db


class TableCardRepository:
    @staticmethod
    def get_table_cards(game_id):
        subquery = db.session.query(CardDB.id, CardDB.rank, CardDB.suit).join(GameCard).filter(GameCard.game_id == game_id).subquery()
        table_cards = db.session.query(subquery).all() #subquery da bi ocuvali duplikate
        table_cards_objects = [CardDB(id=row[0], rank=row[1], suit=row[2]) for row in table_cards]
        return table_cards_objects

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
