from gme.game_logic.model.card_count import CardCount
from gme.repositories.game_repository import GameRepository
from gme.utils import random_cards, validate_points


class GameService:
    @staticmethod
    def accept_invitation(player1_email, player2_email, game):
        player1_from_db = GameService.get_user(player1_email)
        player2_from_db = GameService.get_user(player2_email)

        [table_cards, cards_left] = random_cards(game.cards, game.rules.number_of_table_cards)
        [player1_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)
        [player2_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)

        new_game = GameRepository.create_game(game.name, player1_from_db.id, game.rules.number_of_rounds, game.rules.number_of_cards_per_round)
        GameRepository.create_game_player(new_game.id, player1_from_db.id)
        GameRepository.create_game_player(new_game.id, player2_from_db.id)

        GameService.create_player_cards(new_game.id, player1_from_db.id, player1_cards)
        GameService.create_player_cards(new_game.id, player2_from_db.id, player2_cards)
        GameService.create_table_cards(new_game.id, table_cards)

        available_cards = [card for card in cards_left if card.count > 0]
        GameService.create_pending_cards(new_game.id, available_cards)

        return table_cards, player1_cards, player2_cards, new_game.id

    @staticmethod
    def finish_move(game_id, selected_table_cards, selected_player_card, player_email):
        user_from_db = GameService.get_user(player_email)

        if len(selected_table_cards) == 0: #ovo je slucaj kada ne treba da se racunaju poeni...
            GameService.create_table_card(game_id, selected_player_card['rank'], selected_player_card['suit'])
            GameService.delete_player_card(user_from_db.id, game_id, selected_player_card['rank'], selected_player_card['suit'])

        else:  # slucaj kada se racunaju poeni al za tablic... posle izmeniti kada se interpretiraju druga pravila
            game_player_from_db = GameRepository.get_game_player(game_id, user_from_db.id)
            game_player_from_db.points += validate_points(selected_table_cards, selected_player_card)
            GameRepository.save_changes()
            GameService.delete_player_card(user_from_db.id, game_id, selected_player_card['rank'], selected_player_card['suit'])
            GameService.delete_table_cards(game_id, selected_table_cards)

        game_players = GameRepository.get_game_players(game_id)
        player1 = next((p for p in game_players if p.user.email == player_email), None)
        player2 = next((p for p in game_players if p.user.email != player_email), None)

        GameRepository.update_current_player(game_id, player2.user.id)

        player1_cards = GameService.get_player_cards(game_id, player1.user.id)
        player2_cards = GameService.get_player_cards(game_id, player2.user.id)
        table_cards = GameService.get_table_cards(game_id)

        game = GameRepository.get_game(game_id)
        if (len(player1_cards) == 0 and len(player2_cards) == 0 and game.number_of_rounds == game.current_round):
            winner = max(game_players, key=lambda player: player.points)
            return table_cards, player1_cards, player2_cards, player1, player2, game_players, winner

        if (len(player1_cards) == 0 and len(player2_cards) == 0): #nova runda...
            pending_cards = GameRepository.get_game_pending_cards(game_id)
            pending_cards_count = [CardCount(pending_card.card, pending_card.count) for pending_card in pending_cards]
            [player1_cards, cards_left] = random_cards(pending_cards_count, game.number_of_cards_per_round)
            [player2_cards, cards_left] = random_cards(cards_left, game.number_of_cards_per_round)

            GameService.remove_pending_cards(game_id, player1_cards)
            GameService.remove_pending_cards(game_id, player2_cards)

            GameRepository.increase_game_round(game_id)

        return table_cards, player1_cards, player2_cards, player1, player2, game_players, None

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
    def delete_table_cards(game_id, cards):
        for card in cards:
            card_from_db = GameRepository.get_or_create_card(card['rank'], card['suit'])
            GameRepository.delete_table_card(game_id, card_from_db.id)

    @staticmethod
    def get_game(game_id):
        return GameRepository.get_game(game_id)

    @staticmethod
    def create_pending_cards(game_id, cards):
        for card in cards:
            card_from_db = GameRepository.get_or_create_card(card.card.rank, card.card.suit)
            GameRepository.create_pending_card(game_id, card_from_db.id, card.count)

    @staticmethod
    def remove_pending_cards(game_id, cards_to_remove):
        for card in cards_to_remove:
            card_from_db = GameRepository.get_or_create_card(card.rank, card.suit)
            GameRepository.remove_pending_card(game_id, card_from_db.id)





