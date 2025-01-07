from gme.repositories.user_repository import UserRepository
from gme.utils import random_cards, hash_password, verify_password


class UserService:
    @staticmethod
    def get_user_by_email_and_password(email, password):
        user = UserRepository.get_user_by_email(email=email)
        if user is None:
            return "User with that email doesn't exist!", 404

        correct_password = verify_password(password, user.password)
        if correct_password is False:
            return "Wrong password", 400
        else:
            return "Successful login", 200


    @staticmethod
    def get_user(email):
        return UserRepository.get_user_by_email(email=email)

    @staticmethod
    def create_user(username, email, password):
        check_user = UserRepository.get_user_by_email(email)
        if check_user is not None:
            return "User with that email already exist!", 409

        hashed_password = hash_password(password)
        user = UserRepository.create_user(username, email, hashed_password)
        return "Successful registration!", 200




