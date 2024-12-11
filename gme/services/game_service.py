from gme.repositories.game_repository import GameRepository
from gme.utils import random_cards


class GameService:
    @staticmethod
    def accept_invitation(player1_email, player2_email, game):
        player1_from_db = GameService.get_user(player1_email)
        player2_from_db = GameService.get_user(player2_email)

        [table_cards, cards_left] = random_cards(game.cards, game.rules.number_of_table_cards)
        [player1_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)
        [player2_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)

        new_game = GameRepository.create_game(game.name, player1_from_db.id)
        GameRepository.create_game_player(new_game.id, player1_from_db.id)
        GameRepository.create_game_player(new_game.id, player2_from_db.id)

        GameService.create_player_cards(new_game.id, player1_from_db.id, player1_cards)
        GameService.create_player_cards(new_game.id, player2_from_db.id, player2_cards)
        GameService.create_table_cards(new_game.id, table_cards)
        return table_cards, player1_cards, player2_cards, new_game.id

    @staticmethod
    def finish_move(game_id, selected_table_cards, selected_player_card, player_email):
        user_from_db = GameService.get_user(player_email)

        if len(selected_table_cards) == 0: #ovo je slucaj kada ne treba da se racunaju poeni...
            rank = selected_player_card['rank']
            suit = selected_player_card['suit']
            GameService.create_table_card(game_id, rank, suit)
            GameService.delete_player_card(user_from_db.id, game_id, rank, suit)

        game_players = GameRepository.get_game_players(game_id)
        player1 = next((p for p in game_players if p.email == player_email), None)
        player2 = next((p for p in game_players if p.email != player_email), None)

        GameRepository.update_current_player(game_id, player2.id)

        player1_cards = GameService.get_player_cards(game_id, player1.id)
        player2_cards = GameService.get_player_cards(game_id, player2.id)
        table_cards = GameService.get_table_cards(game_id)

        return table_cards, player1_cards, player2_cards, player2.email

    @staticmethod
    def get_user_by_email_and_password(email, password):
        return GameRepository.get_user_by_email_and_password(email=email, password=password)
    @staticmethod
    def get_user(email):
        return GameRepository.get_user(email=email)
    @staticmethod
    def get_player_cards(game_id, user_id):
        return GameRepository.get_player_cards(game_id=game_id, user_id=user_id)
    @staticmethod
    def get_table_cards(game_id):
        return GameRepository.get_table_cards(game_id=game_id)

    @staticmethod
    def create_table_cards(game_id, cards):
        for card in cards:
            GameService.create_table_card(game_id, card.rank, card.suit)

    @staticmethod
    def create_table_card(game_id, card_rank, card_suit):
        card_from_db = GameRepository.get_or_create_card(card_rank, card_suit)
        GameRepository.create_table_card(game_id, card_from_db.id)

    @staticmethod
    def create_player_cards(game_id, user_id, cards):
        for card in cards:
            GameService.create_player_card(game_id, user_id, card.rank, card.suit)

    @staticmethod
    def create_player_card(game_id, user_id, card_rank, card_suit):
        card_from_db = GameRepository.get_or_create_card(card_rank, card_suit)
        GameRepository.create_player_card(game_id, user_id, card_from_db.id)

    @staticmethod
    def delete_player_card(user_id, game_id, card_rank, card_suit):
        card_from_db = GameRepository.get_or_create_card(card_rank, card_suit)
        GameRepository.delete_player_card(user_id, game_id, card_from_db.id)

    @staticmethod
    def get_game(game_id):
        return GameRepository.get_game(game_id)

