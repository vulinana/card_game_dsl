from sqlalchemy import func, desc
from sqlalchemy.orm import joinedload

from models import GameDB, Round, User
from extensions import db


class RoundRepository:
    @staticmethod
    def create_new_round(game_id, round_initiator_id):
        # Pronaći najveći broj runde za dati game_id
        last_round = db.session.query(func.max(Round.number)).filter_by(game_id=game_id).scalar()

        # Ako nije pronađena nijedna runda, postaviti broj na 1, inače uvećati za 1
        new_round_number = 1 if last_round is None else last_round + 1

        # Kreirati novu rundu
        new_round = Round(
            number=new_round_number,
            game_id=game_id,
            round_initiator_id=round_initiator_id
        )

        db.session.add(new_round)
        db.session.commit()
        return new_round

    @staticmethod
    def get_current_round(game_id):
        current_round = (
            db.session.query(Round)
            .filter_by(game_id=game_id)
            .order_by(desc(Round.number))
            .first()
        )
        return current_round

    @staticmethod
    def get_previous_round(game_id):
        last_round = (
            db.session.query(Round)
            .filter_by(game_id=game_id)
            .order_by(desc(Round.number))
            .first()
        )

        if last_round:
            previous_round = (
                db.session.query(Round)
                .filter_by(game_id=game_id)
                .filter(Round.number == last_round.number - 1)
                .join(User, User.id == Round.winner_id)
                .first()
            )
            return previous_round
        return None

    @staticmethod
    def update_current_round_initiator(game_id, round_initiator_id):
        current_round = RoundRepository.get_current_round(game_id)
        current_round.round_initiator_id = round_initiator_id
        db.session.commit()

