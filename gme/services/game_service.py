from gme.model.card_count import CardCount
from gme.repositories.action_repository import ActionRepository
from gme.repositories.card_repository import CardRepository
from gme.repositories.game_player_repository import GamePlayerRepository
from gme.repositories.game_repository import GameRepository
from gme.repositories.game_request_repository import GameRequestRepository
from gme.repositories.pending_card_repository import PendingCardRepository
from gme.repositories.played_card_repository import PlayedCardRepository
from gme.repositories.player_card_repository import PlayerCardRepository
from gme.repositories.round_repository import RoundRepository
from gme.repositories.table_card_repository import TableCardRepository
from gme.repositories.user_repository import UserRepository
from gme.utils import random_cards, get_valid_card_combinations_by_rank, load_games_shared
from models import GameRequestStatus


class GameService:
    @staticmethod
    def create_game_init(game_name, game_initiator_email, rivals):
        game_initiator = UserRepository.get_user_by_email(email=game_initiator_email)
        game = next((game for game in load_games_shared() if game.name == game_name), None)
        new_game = GameRepository.create_game_init(game_name, game_initiator, game.rules.min_number_of_players, game.rules.max_number_of_players)
        for rival_email in rivals:
            rival = UserRepository.get_user_by_email(email=rival_email)
            GameRequestRepository.create_game_request(new_game.id, rival.id)
        return new_game

    @staticmethod
    def start_game(game_id, game):
        game_from_db = GameRepository.get_game(game_id)

        game_from_db.current_player_id = game_from_db.game_initiator.id
        game_from_db.number_of_rounds = game.rules.number_of_rounds
        game_from_db.number_of_cards_per_round = game.rules.number_of_cards_per_round
        game_from_db.winner_condition = game.rules.winner_condition
        game_from_db.new_round_condition = game.rules.new_round_condition
        game_from_db.next_player_in_round_condition = game.rules.next_player_in_round_condition
        GameRepository.save_changes()

        RoundRepository.create_new_round(game_id, game_from_db.game_initiator_id)

        # dodati akcije u igru
        for action in game.actions:
            ActionRepository.create(game_from_db.id, action.action_type)

        # dodati karte u igru
        for card in game.cards:
            CardRepository.create(game_from_db.id, card.card.rank, card.card.suit, card.score)

        [table_cards, cards_left] = random_cards(game.cards, game.rules.number_of_table_cards)
        GameService.create_table_cards(game_from_db.id, table_cards)

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
        current_player = UserRepository.get_user_by_email(player_email)
        game = GameRepository.get_game(game_id)
        game_players = GamePlayerRepository.get_game_players(game_id)

        is_new_round = GameService.is_new_round(game)
        GameService.take_action(game, current_player, selected_player_card, selected_table_cards, is_new_round)
        winner = GameService.get_winner(game, game_players)
        GameService.new_round(game, game_players)
        GameService.next_player(game, game_players, is_new_round)

        #pribavi karte
        player_cards_data = GameService.get_players_cards_data(game_id)
        table_cards = GameService.get_table_cards(game_id)

        return [card.to_dict() for card in table_cards], player_cards_data, winner

    @staticmethod
    def get_winner(game, game_players):
        if not PlayerCardRepository.any_player_has_cards(
                game.id) and game.number_of_rounds == RoundRepository.get_current_round(game.id).number:
            if game.winner_condition == 'highest_score':
                return max(game_players, key=lambda player: player.points)
            if game.winner_condition == 'lowest_score':
                return min(game_players, key=lambda player: player.points)
        return None

    @staticmethod
    def is_new_round(game):
        if game.new_round_condition == 'no_cards_left':
            if not PlayerCardRepository.any_player_has_cards(game.id):
                return True
        if game.new_round_condition == 'circle_completed':
            game_players = GamePlayerRepository.get_game_players(game.id)
            if GameService.get_next_player_circle_order(game, game_players).id == RoundRepository.get_current_round(
                    game.id).round_initiator_id:
                return True
        return False

    @staticmethod
    def new_round(game, game_players):
        if game.new_round_condition == 'no_cards_left':
            if not PlayerCardRepository.any_player_has_cards(game.id):
                for player in game_players:
                    pending_cards = PendingCardRepository.get_game_pending_cards(game.id)
                    pending_cards_count = [CardCount(pending_card.card, 0, pending_card.count) for pending_card in
                                           pending_cards]
                    [player_cards, cards_left] = random_cards(pending_cards_count, game.number_of_cards_per_round)
                    GameService.remove_pending_cards(game.id, player_cards)
                    GameService.create_player_cards(game.id, player.user.id, player_cards)

                RoundRepository.create_new_round(game.id, None)

        if game.new_round_condition == 'circle_completed':  # dopunjavamo do number_of_cards_per_round...
            if GameService.get_next_player_circle_order(game, game_players).id == RoundRepository.get_current_round(
                    game.id).round_initiator_id:
                for player in game_players:
                    old_player_cards = GameService.get_player_cards(game.id, player.user.id)
                    pending_cards = PendingCardRepository.get_game_pending_cards(game.id)
                    pending_cards_count = [CardCount(pending_card.card, 0, pending_card.count) for pending_card in
                                           pending_cards]
                    [new_player_cards, cards_left] = random_cards(pending_cards_count,
                                                                  game.number_of_cards_per_round - len(
                                                                      old_player_cards))
                    GameService.remove_pending_cards(game.id, new_player_cards)
                    GameService.create_player_cards(game.id, player.user.id, new_player_cards)

                RoundRepository.create_new_round(game.id, None)


    @staticmethod
    def next_player(game, game_players, is_new_round):
        if not is_new_round:
            next_player = GameService.get_next_player_circle_order(game, game_players)
        else:
            if game.next_player_in_round_condition == "winner":
                next_player = RoundRepository.get_previous_round(game.id).winner
            else:
                next_player = GameService.get_next_player_circle_order(game, game_players)
            RoundRepository.update_current_round_initiator(game.id, next_player.id)

        GameRepository.update_current_player(game.id, next_player.id)

    @staticmethod
    def take_action(game, current_player, selected_player_card, selected_table_cards, is_new_round):
        action = ActionRepository.get_by_game_id(game.id)

        if action.action_type == "follow_by_rank" or action.action_type == "follow_by_suit" or action.action_type == 'follow_by_rank_or_suit':
            #zabeleziti odigrane karte...
            card_from_db = CardRepository.get(game.id, selected_player_card['rank'], selected_player_card['suit'])
            current_round = RoundRepository.get_current_round(game.id)
            PlayedCardRepository.create_played_card(current_player.id, game.id, card_from_db.id, current_round.id)
            if is_new_round:
                TableCardRepository.delete_all_by_game_id(game.id)

                #who is winner?
                played_cards = PlayedCardRepository.get_played_cards_by_game_id_and_round_id(game.id, current_round.id)
                initiator_card = next(
                    (card for card in played_cards if card.user_id == current_round.round_initiator_id), None
                )
                remaining_cards = [card for card in played_cards if card != initiator_card]
                if action.action_type == "follow_by_rank":
                    matching_rank_cards = [card for card in remaining_cards if
                                           card.card.rank == initiator_card.card.rank]

                elif action.action_type == 'follow_by_suit':
                    matching_rank_cards = [card for card in remaining_cards if
                                           card.card.suit == initiator_card.card.suit]
                else:
                    matching_rank_cards = [card for card in remaining_cards if
                                           (
                                                       card.card.rank == initiator_card.card.rank or card.card.suit == initiator_card.card.suit)]
                if matching_rank_cards:
                    current_round.winner_id = matching_rank_cards[
                        -1].user_id  # poslednji koji je igrao ovo testirati..
                else:
                    current_round.winner_id = initiator_card.user_id
                    GameRepository.save_changes()

                #winner dobija poene sve koji su played card za tu rundu...
                game_player_from_db = GamePlayerRepository.get_game_player(game.id, current_round.winner_id)
                game_player_from_db.points += GameService.calculate_points(game.id, [played_card.card.to_dict() for played_card in played_cards])
                GameRepository.save_changes()

            else:
                GameService.delete_player_card(current_player.id, game.id, selected_player_card['rank'],
                                               selected_player_card['suit'])
                GameService.create_table_card(game.id, selected_player_card['rank'], selected_player_card['suit'])

        if action.action_type == "collect_by_rank":
            if len(selected_table_cards) == 0:  # ovo je slucaj kada ne treba da se racunaju poeni...
                GameService.create_table_card(game.id, selected_player_card['rank'], selected_player_card['suit'])
                GameService.delete_player_card(current_player.id, game.id, selected_player_card['rank'],
                                               selected_player_card['suit'])

            else:
                game_player_from_db = GamePlayerRepository.get_game_player(game.id, current_player.id)
                valid_cards, invalid_cards = get_valid_card_combinations_by_rank(selected_player_card, selected_table_cards)
                game_player_from_db.points += GameService.calculate_points(game.id, valid_cards)
                GameRepository.save_changes()
                GameService.delete_player_card(current_player.id, game.id, selected_player_card['rank'],
                                               selected_player_card['suit'])
                GameService.delete_table_cards(game.id, selected_table_cards)

    @staticmethod
    def calculate_points(game_id, cards):
        points = 0
        for card in cards:
            points += CardRepository.get(game_id, card['rank'], card['suit']).score

        return points

    @staticmethod
    def get_next_player_circle_order(game, game_players):
        current_index = next(i for i, player in enumerate(game_players) if player.user.id == game.current_player.id)
        next_index = (current_index + 1) % len(
            game_players)  # Kružni redosled, ako smo na poslednjem igraču, vraćamo se na prvog
        next_player = game_players[next_index].user
        return next_player

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
        return TableCardRepository.get_table_cards(game_id=game_id)

    @staticmethod
    def create_table_cards(game_id, cards):
        for card in cards:
            GameService.create_table_card(game_id, card.rank, card.suit)

    @staticmethod
    def create_table_card(game_id, card_rank, card_suit):
        card_from_db = CardRepository.get(game_id, card_rank, card_suit)
        TableCardRepository.create_table_card(game_id, card_from_db.id)

    @staticmethod
    def create_player_cards(game_id, user_id, cards):
        for card in cards:
            GameService.create_player_card(game_id, user_id, card.rank, card.suit)

    @staticmethod
    def create_player_card(game_id, user_id, card_rank, card_suit):
        card_from_db = CardRepository.get(game_id, card_rank, card_suit)
        PlayerCardRepository.create_player_card(game_id, user_id, card_from_db.id)

    @staticmethod
    def delete_player_card(user_id, game_id, card_rank, card_suit):
        card_from_db = CardRepository.get(game_id, card_rank, card_suit)
        PlayerCardRepository.delete_player_card(user_id, game_id, card_from_db.id)

    @staticmethod
    def delete_table_cards(game_id, cards):
        for card in cards:
            card_from_db = CardRepository.get(game_id, card['rank'], card['suit'])
            TableCardRepository.delete_table_card(game_id, card_from_db.id)

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
