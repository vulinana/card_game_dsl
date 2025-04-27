from gme.repositories.card_repository import CardRepository
from gme.repositories.game_player_repository import GamePlayerRepository
from gme.repositories.game_repository import GameRepository
from gme.repositories.game_request_repository import GameRequestRepository
from gme.repositories.pending_card_repository import PendingCardRepository
from gme.repositories.player_card_repository import PlayerCardRepository
from gme.repositories.round_repository import RoundRepository
from gme.repositories.table_card_repository import TableCardRepository
from gme.repositories.user_repository import UserRepository
from gme.utils import load_games_shared
from models import GameRequestStatus


class GameService:
    @staticmethod
    def create_game_init(game_name, game_initiator_email, rivals):
        game_initiator = UserRepository.get_user_by_email(email=game_initiator_email)
        game = next((game for game in load_games_shared() if game.name == game_name), None)
        new_game = GameRepository.create_game_init(game_name, game_initiator, [game.states[0].name])
        for rival_email in rivals:
            rival = UserRepository.get_user_by_email(email=rival_email)
            GameRequestRepository.create_game_request(new_game.id, rival.id)
        RoundRepository.create_new_round(new_game.id, game_initiator.id)
        for card in game.cards:
            CardRepository.create(new_game.id, card.card.rank, card.card.suit, card.score)
        GameService.create_pending_cards(new_game.id, game.cards)
        return new_game

    @staticmethod
    def create_game_players(game_id):
        game_from_db = GameRepository.get_game(game_id)
        for game_request in game_from_db.game_requests:
            if game_request.status == GameRequestStatus.ACCEPTED:
                player_id = game_request.user_id
                GamePlayerRepository.create_game_player(game_id, player_id)

        player_id = game_from_db.game_initiator.id
        GamePlayerRepository.create_game_player(game_id, player_id)

    @staticmethod
    def get_game_players(game_id):
        return GamePlayerRepository.get_game_players(game_id)

    @staticmethod
    def get_players_cards_data(game_id):
        player_cards_data = []
        game_players = GamePlayerRepository.get_game_players(game_id)
        for player in game_players:
            player_cards = GameService.get_player_cards(game_id, player.user.id)
            player_cards_data.append({
                'player_email': player.user.email,
                'cards': [card.to_dict() for card in player_cards],
                'points': player.points
            })
        return player_cards_data


    @staticmethod
    def get_player_cards(game_id, user_id):
        return PlayerCardRepository.get_player_cards(game_id=game_id, user_id=user_id)

    @staticmethod
    def get_table_cards(game_id):
        table_cards = TableCardRepository.get_table_cards(game_id=game_id)
        return [card.to_dict() for card in table_cards]

    @staticmethod
    def create_table_cards(game_id, cards, visible):
        for card in cards:
            GameService.create_table_card(game_id, card.rank, card.suit, visible)

    @staticmethod
    def create_table_card(game_id, card_rank, card_suit, visible):
        card_from_db = CardRepository.get(game_id, card_rank, card_suit)
        TableCardRepository.create_table_card(game_id, card_from_db.id, visible)

    @staticmethod
    def create_player_cards(game_id, user_id, cards):
        for card in cards:
            GameService.create_player_card(game_id, user_id, card.rank, card.suit)

    @staticmethod
    def create_player_card(game_id, user_id, card_rank, card_suit):
        card_from_db = CardRepository.get(game_id, card_rank, card_suit)
        PlayerCardRepository.create_player_card(game_id, user_id, card_from_db.id)

    @staticmethod
    def get_game(game_id):
        return GameRepository.get_game(game_id)

    @staticmethod
    def create_pending_cards(game_id, cards):
        for card in cards:
            card_from_db = CardRepository.get(game_id, card.card.rank, card.card.suit)
            PendingCardRepository.create_pending_card(game_id, card_from_db.id, card.count)

    @staticmethod
    def remove_pending_cards(game_id, cards_to_remove):
        for card in cards_to_remove:
            card_from_db = CardRepository.get(game_id, card.rank, card.suit)
            PendingCardRepository.remove_pending_card(game_id, card_from_db.id)

    @staticmethod
    def update_game_request_status(game_id, user_id, status):
        GameRequestRepository.update_game_request_status(game_id, user_id, status)

    @staticmethod
    def update_next_states(game_id, next_states):
        GameRepository.update_next_states(game_id, next_states)
    @staticmethod
    def find_next_states(game_id, current_state, condition):
        condition = "true" if condition else "false"
        next_states = []
        for t in current_state.transitions:
            t_condition = t.condition

            if not t_condition:
                next_states.append(t.nextState)
            elif condition and condition == t_condition:
                next_states.append(t.nextState)
        GameRepository.update_next_states(game_id, next_states)

    @staticmethod
    def get_current_round(game_id):
        return RoundRepository.get_current_round(game_id)
