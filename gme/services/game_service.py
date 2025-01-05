from gme.game_logic.model.card_count import CardCount
from gme.repositories.card_repository import CardRepository
from gme.repositories.game_player_repository import GamePlayerRepository
from gme.repositories.game_repository import GameRepository
from gme.repositories.game_request_repository import GameRequestRepository
from gme.repositories.pending_card_repository import PendingCardRepository
from gme.repositories.player_card_repository import PlayerCardRepository
from gme.repositories.table_card_repository import TableCardRepository
from gme.repositories.user_repository import UserRepository
from gme.utils import random_cards, validate_points, hash_password, verify_password
from models import GameRequestStatus


class GameService:
    @staticmethod
    def create_game_init(game_name, game_initiator_email, rivals):
        game_initiator = UserRepository.get_user_by_email(email=game_initiator_email)
        new_game = GameRepository.create_game_init(game_name, game_initiator)
        for rival_email in rivals:
            rival = UserRepository.get_user_by_email(email=rival_email)
            GameRequestRepository.create_game_request(new_game.id, rival.id)
        return new_game

    @staticmethod
    def start_game(game_id, game):
        game_from_db = GameRepository.get_game(game_id)
        [table_cards, cards_left] = random_cards(game.cards, game.rules.number_of_table_cards)
        GameService.create_table_cards(game_from_db.id, table_cards)

        #potrebno apdejtovati igru...
        game_from_db.current_player_id = game_from_db.game_initiator.id
        game_from_db.current_round = 1
        game_from_db.number_of_rounds = game.rules.number_of_rounds
        game_from_db.number_of_cards_per_round = game.rules.number_of_cards_per_round
        GameRepository.save_changes()

        player_cards_data = []

        [player_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)
        player_id = game_from_db.game_initiator.id
        GamePlayerRepository.create_game_player(game_id, player_id)
        GameService.create_player_cards(game_id, player_id, player_cards)

        player = UserRepository.get_user_by_id(player_id)
        player_cards_data.append({
            'player_email': player.email,
            'cards': [card.to_dict() for card in player_cards],
            'points': 0
        })


        for game_request in game_from_db.game_requests:
            if game_request.status == GameRequestStatus.ACCEPTED:
                [player_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)
                player_id = game_request.user_id
                GamePlayerRepository.create_game_player(game_id, player_id)
                GameService.create_player_cards(game_id, player_id, player_cards)

                player = UserRepository.get_user_by_id(player_id)
                player_cards_data.append({
                    'player_email': player.email,
                    'cards': [card.to_dict() for card in player_cards],
                    'points': 0
                })

        available_cards = [card for card in cards_left if card.count > 0]
        GameService.create_pending_cards(game_id, available_cards)

        return [card.to_dict() for card in table_cards], player_cards_data


    @staticmethod
    def finish_move(game_id, selected_table_cards, selected_player_card, player_email):
        user_from_db = GameService.get_user(player_email)

        print("selected_table_Cards,", selected_table_cards)
        if len(selected_table_cards) == 0: #ovo je slucaj kada ne treba da se racunaju poeni...
            GameService.create_table_card(game_id, selected_player_card['rank'], selected_player_card['suit'])
            GameService.delete_player_card(user_from_db.id, game_id, selected_player_card['rank'], selected_player_card['suit'])

        else:  # slucaj kada se racunaju poeni al za tablic... posle izmeniti kada se interpretiraju druga pravila
            game_player_from_db = GamePlayerRepository.get_game_player(game_id, user_from_db.id)
            game_player_from_db.points += validate_points(selected_table_cards, selected_player_card)
            GameRepository.save_changes()
            GameService.delete_player_card(user_from_db.id, game_id, selected_player_card['rank'], selected_player_card['suit'])
            GameService.delete_table_cards(game_id, selected_table_cards)

        player_cards_data = []
        game_players = GamePlayerRepository.get_game_players(game_id)
        for player in game_players:
            player_cards = GameService.get_player_cards(game_id, player.user.id)
            player_cards_data.append({
                'player_email': player.user.email,
                'cards': [card.to_dict() for card in player_cards],
                'points': player.points
            })

        game = GameRepository.get_game(game_id)

        #next player?
        current_index = next(i for i, player in enumerate(game_players) if player.user.id == game.current_player.id)
        next_index = (current_index + 1) % len(game_players)  # Kružni redosled, ako smo na poslednjem igraču, vraćamo se na prvog
        next_player_id = game_players[next_index].user.id
        GameRepository.update_current_player(game_id, next_player_id)

        table_cards = GameService.get_table_cards(game_id)

        if not any(player["cards"] for player in player_cards_data) and game.number_of_rounds == game.current_round:
            winner = max(game_players, key=lambda player: player.points)
            return [card.to_dict() for card in table_cards], player_cards_data, winner


        if not any(player["cards"] for player in player_cards_data): #nova runda...
            player_cards_data = []
            for player in game_players:
                pending_cards = PendingCardRepository.get_game_pending_cards(game_id)
                pending_cards_count = [CardCount(pending_card.card, pending_card.count) for pending_card in
                                       pending_cards]
                [player_cards, cards_left] = random_cards(pending_cards_count, game.number_of_cards_per_round)
                GameService.remove_pending_cards(game_id, player_cards)

                player_cards_data.append({
                    'player_email': player.user.email,
                    'cards': [card.to_dict() for card in player_cards],
                    'points': player.points
                })

            GameRepository.increase_game_round(game_id)

        return [card.to_dict() for card in table_cards], player_cards_data, None

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
    def get_player_cards(game_id, user_id):
        return PlayerCardRepository.get_player_cards(game_id=game_id, user_id=user_id)
    @staticmethod
    def get_table_cards(game_id):
        return TableCardRepository.get_table_cards(game_id=game_id)

    @staticmethod
    def create_table_cards(game_id, cards):
        for card in cards:
            GameService.create_table_card(game_id, card.rank, card.suit)

    @staticmethod
    def create_table_card(game_id, card_rank, card_suit):
        card_from_db = CardRepository.get_or_create_card(card_rank, card_suit)
        TableCardRepository.create_table_card(game_id, card_from_db.id)

    @staticmethod
    def create_player_cards(game_id, user_id, cards):
        for card in cards:
            GameService.create_player_card(game_id, user_id, card.rank, card.suit)

    @staticmethod
    def create_player_card(game_id, user_id, card_rank, card_suit):
        card_from_db = CardRepository.get_or_create_card(card_rank, card_suit)
        PlayerCardRepository.create_player_card(game_id, user_id, card_from_db.id)

    @staticmethod
    def delete_player_card(user_id, game_id, card_rank, card_suit):
        card_from_db = CardRepository.get_or_create_card(card_rank, card_suit)
        PlayerCardRepository.delete_player_card(user_id, game_id, card_from_db.id)

    @staticmethod
    def delete_table_cards(game_id, cards):
        for card in cards:
            card_from_db = CardRepository.get_or_create_card(card['rank'], card['suit'])
            TableCardRepository.delete_table_card(game_id, card_from_db.id)

    @staticmethod
    def get_game(game_id):
        return GameRepository.get_game(game_id)

    @staticmethod
    def create_pending_cards(game_id, cards):
        for card in cards:
            card_from_db = CardRepository.get_or_create_card(card.card.rank, card.card.suit)
            PendingCardRepository.create_pending_card(game_id, card_from_db.id, card.count)

    @staticmethod
    def remove_pending_cards(game_id, cards_to_remove):
        for card in cards_to_remove:
            card_from_db = CardRepository.get_or_create_card(card.rank, card.suit)
            PendingCardRepository.remove_pending_card(game_id, card_from_db.id)

    @staticmethod
    def update_game_request_status(game_id, user_id, status):
        GameRequestRepository.update_game_request_status(game_id, user_id, status)

    @staticmethod
    def create_user(username, email, password):
        check_user = UserRepository.get_user_by_email(email)
        if check_user is not None:
            return "User with that email already exist!", 409

        hashed_password = hash_password(password)
        user = UserRepository.create_user(username, email, hashed_password)
        return "Successful registration!", 200




