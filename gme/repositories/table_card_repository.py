from models import CardDB, TableCard
from extensions import db


class TableCardRepository:
    @staticmethod
    def get_table_cards(game_id):
        subquery = db.session.query(CardDB.id, CardDB.rank, CardDB.suit).join(TableCard).filter(TableCard.game_id == game_id).subquery()
        table_cards = db.session.query(subquery).all() #subquery da bi ocuvali duplikate
        table_cards_objects = [CardDB(id=row[0], rank=row[1], suit=row[2]) for row in table_cards]
        return table_cards_objects

    @staticmethod
    def create_table_card(game_id, card_id):
        new_game_card = TableCard(game_id=game_id,
                                 card_id=card_id)
        db.session.add(new_game_card)
        db.session.commit()

    @staticmethod
    def delete_table_card(game_id, card_id):
        table_card_from_db = TableCard.query.filter_by(game_id=game_id, card_id=card_id).first()
        db.session.delete(table_card_from_db)
        db.session.commit()

    @staticmethod
    def delete_all_by_game_id(game_id):
        TableCard.query.filter_by(game_id=game_id).delete()
        db.session.commit()
