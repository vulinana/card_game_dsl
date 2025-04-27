from models import CardDB, TableCard
from extensions import db


class TableCardRepository:
    @staticmethod
    def get_table_cards(game_id):
        table_cards = (
            db.session.query(TableCard)
            .join(CardDB, TableCard.card)
            .filter(TableCard.game_id == game_id)
            .order_by(TableCard.id)
            .all()
        )
        return table_cards

    @staticmethod
    def get(id):
        return db.session.query(TableCard).join(CardDB, TableCard.card).filter(TableCard.id == id).first()

    @staticmethod
    def create_table_card(game_id, card_id, visible):
        new_game_card = TableCard(game_id=game_id,
                                 card_id=card_id,
                                 visible=visible)
        db.session.add(new_game_card)
        db.session.commit()

    @staticmethod
    def delete_table_card(game_id, card_id):
        table_card_from_db = TableCard.query.filter_by(game_id=game_id, card_id=card_id).first()
        print("table card from db ", table_card_from_db)
        db.session.delete(table_card_from_db)
        db.session.commit()

    @staticmethod
    def delete_table_card_by_id(id):
        table_card_from_db = TableCard.query.filter_by(id=id).first()
        print("table card from db ", table_card_from_db)
        db.session.delete(table_card_from_db)
        db.session.commit()

    @staticmethod
    def delete_all_by_game_id(game_id):
        TableCard.query.filter_by(game_id=game_id).delete()
        db.session.commit()

    @staticmethod
    def update_table_card_visibility(id, visibility):
        card = TableCard.query.filter_by(id=id).first()
        card.visible = visibility
        db.session.commit()




