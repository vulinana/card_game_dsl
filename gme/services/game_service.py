from gme.game_logic.model.card_count import CardCount
from gme.repositories.game_repository import GameRepository
from gme.utils import random_cards, validate_points
from models import GameRequestStatus


class GameService:
    @staticmethod
    def create_game_init(game_name, game_initiator_email, rivals):
        game_initiator = GameRepository.get_user(email=game_initiator_email)
        new_game = GameRepository.create_game_init(game_name, game_initiator)
        for rival_email in rivals:
            rival = GameRepository.get_user(email=rival_email)
            GameRepository.create_game_request(new_game.id, rival.id)
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
        GameRepository.create_game_player(game_id, player_id)
        GameService.create_player_cards(game_id, player_id, player_cards)

        player = GameRepository.get_user_by_id(player_id)
        player_cards_data.append({
            'player_email': player.email,
            'cards': [card.to_dict() for card in player_cards],
            'points': 0
        })


        for game_request in game_from_db.game_requests:
            if game_request.status == GameRequestStatus.ACCEPTED:
                [player_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)
                player_id = game_request.user_id
                GameRepository.create_game_player(game_id, player_id)
                GameService.create_player_cards(game_id, player_id, player_cards)

                player = GameRepository.get_user_by_id(player_id)
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
            game_player_from_db = GameRepository.get_game_player(game_id, user_from_db.id)
            game_player_from_db.points += validate_points(selected_table_cards, selected_player_card)
            GameRepository.save_changes()
            GameService.delete_player_card(user_from_db.id, game_id, selected_player_card['rank'], selected_player_card['suit'])
            GameService.delete_table_cards(game_id, selected_table_cards)

        player_cards_data = []
        game_players = GameRepository.get_game_players(game_id)
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
                pending_cards = GameRepository.get_game_pending_cards(game_id)
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

    @staticmethod
    def update_game_request_status(game_id, user_id, status):
        GameRepository.update_game_request_status(game_id, user_id, status)




