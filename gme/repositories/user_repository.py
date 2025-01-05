from models import User
from extensions import db


class UserRepository:
    @staticmethod
    def get_user_by_email_and_password(email, password):
        return (
            User.query.filter_by(email=email, password=password).first()
        )
    @staticmethod
    def get_user_by_email(email):
        return (
            User.query.filter_by(email=email).first()
        )

    @staticmethod
    def get_user_by_id(id):
        return (
            User.query.filter_by(id=id).first()
        )

    @staticmethod
    def create_user(username, email, password):
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return new_user