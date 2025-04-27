from gme.model.card_count import CardCount
from gme.repositories.card_repository import CardRepository
from gme.repositories.game_player_repository import GamePlayerRepository
from gme.repositories.game_repository import GameRepository
from gme.repositories.pending_card_repository import PendingCardRepository
from gme.repositories.player_card_repository import PlayerCardRepository
from gme.repositories.round_repository import RoundRepository
from gme.repositories.table_card_repository import TableCardRepository
from gme.repositories.user_repository import UserRepository
from gme.repositories.valid_card_repository import ValidCardRepository
from gme.services.game_service import GameService
from gme.utils import random_cards, get_valid_card_combinations_by_rank
from models import CardTypeEnum


class StateService:
    @staticmethod
    def deal_table_cards(number, game, game_id):
        pending_cards = PendingCardRepository.get_game_pending_cards(game_id)
        if len(pending_cards) == 0:
            return
        cards = [CardCount(pending_card.card, 0, pending_card.count) for pending_card in
                 pending_cards]
        [table_cards, cards_left] = random_cards(cards, number)
        GameService.create_table_cards(game_id, table_cards, game.rules.table_cards_visible)
        GameService.remove_pending_cards(game_id, table_cards)

    @staticmethod
    def deal_player_cards(number, game_id):
        pending_cards = PendingCardRepository.get_game_pending_cards(game_id)
        if len(pending_cards) == 0:
            return
        cards = [CardCount(pending_card.card, 0, pending_card.count) for pending_card in
                               pending_cards]

        players = GameService.get_game_players(game_id)
        for player in players:
            [player_cards, cards_left] = random_cards(cards, number)
            GameService.create_player_cards(game_id, player.user.id, player_cards)
            GameService.remove_pending_cards(game_id, player_cards)
            cards = cards_left

    @staticmethod
    def fill_player_hand_to(game_id, max_number):
        pending_cards = PendingCardRepository.get_game_pending_cards(game_id)
        if len(pending_cards) == 0:
            return
        cards = [CardCount(pending_card.card, 0, pending_card.count) for pending_card in
                 pending_cards]

        players = GameService.get_game_players(game_id)
        for player in players:
            old_player_cards = PlayerCardRepository.get_player_cards(game_id, player.user.id)
            number = max_number - len(old_player_cards)
            [new_player_cards, cards_left] = random_cards(cards, number)
            GameService.create_player_cards(game_id, player.user.id, new_player_cards)
            GameService.remove_pending_cards(game_id, new_player_cards)
            cards = cards_left

    @staticmethod
    def next_player(game_id, is_new_round, next_player_in_round_condition):
        game_players = GameService.get_game_players(game_id)
        game_from_db = GameService.get_game(game_id)
        if not is_new_round:
            next_player = StateService.get_next_player_circle_order(game_from_db, game_players)
        else:
            if next_player_in_round_condition == 'circle_order':
                next_player = StateService.get_next_player_circle_order(game_from_db, game_players)
            else: #last_played
               return game_from_db.current_player.email

        GameRepository.update_current_player(game_id, next_player.id)
        return next_player.email

    @staticmethod
    def get_next_player_circle_order(game, game_players):
        current_index = next(i for i, player in enumerate(game_players) if player.user.id == game.current_player.id)
        next_index = (current_index + 1) % len(
            game_players)  # Kružni redosled, ako smo na poslednjem igraču, vraćamo se na prvog
        next_player = game_players[next_index].user
        return next_player

    @staticmethod
    def throw_cards(game_id, selected_player_card):
        GameService.create_table_card(game_id, selected_player_card['rank'], selected_player_card['suit'], True)
        PlayerCardRepository.delete_player_card_by_id(selected_player_card['id'])

    @staticmethod
    def check_if_any_players_cards(game_id):
        return PlayerCardRepository.any_player_has_cards(game_id)

    @staticmethod
    def cards_selection_sum_matching(selected_player_card, selected_table_cards):
        valid_cards, invalid_cards = get_valid_card_combinations_by_rank(selected_player_card, selected_table_cards)

        if len(invalid_cards) != 0:
            return []

        selected_player_card["card_type"] = CardTypeEnum.PLAYER_CARD

        for card in selected_table_cards:
            card["card_type"] = CardTypeEnum.TABLE_CARD

        matching_cards = [selected_player_card] + selected_table_cards
        return matching_cards

    @staticmethod
    def calculate_points(game_id):
        valid_cards = ValidCardRepository.get_valid_cards_by_game_id(game_id)

        points_by_user = {}

        for card in valid_cards:
            user_id = card.user_id
            if user_id not in points_by_user:
                points_by_user[user_id] = 0

            if card.card_type == CardTypeEnum.PLAYER_CARD:
                player_card = PlayerCardRepository.get(card.card_id)
                score = player_card.card.score
            else:
                table_card = TableCardRepository.get(card.card_id)
                score = table_card.card.score

            points_by_user[user_id] += score

        for user_id, points in points_by_user.items():
            if points > 0:
                GamePlayerRepository.update_player_points(user_id, game_id, points)


    @staticmethod
    def remove_selected_cards(game_id):
        valid_cards = ValidCardRepository.get_valid_cards_by_game_id(game_id)
        for card in valid_cards:
            if card.card_type == CardTypeEnum.PLAYER_CARD:
                PlayerCardRepository.delete_player_card_by_id(card.card_id)
            else:
                TableCardRepository.delete_table_card_by_id(card.card_id)
        ValidCardRepository.remove_valid_cards(game_id)

    @staticmethod
    def new_round(game_id):
        RoundRepository.create_new_round(game_id, None)

    @staticmethod
    def check_if_rounds_remaining(game_id, max_rounds):
        return RoundRepository.get_current_round(game_id).number <= max_rounds

    @staticmethod
    def determine_game_winner(game_id, game_winner_condition):
        game_players = GameService.get_game_players(game_id)
        winners = []
        if game_winner_condition == 'highest_score':
            max_points = max(game_players, key=lambda player: player.points).points
            winners = [player for player in game_players if player.points == max_points]
        if game_winner_condition == 'lowest_score':
            min_points = min(game_players, key=lambda player: player.points).points
            winners = [player for player in game_players if player.points == min_points]
        return winners

    @staticmethod
    def any_matching_table_cards(game_id, match_by):
        table_cards = TableCardRepository.get_table_cards(game_id)

        for i in range(len(table_cards)):
            for j in range(i + 1, len(table_cards)):
                card1 = table_cards[i].card
                card2 = table_cards[j].card

                rank_match = card1.rank == card2.rank
                suit_match = card1.suit == card2.suit

                if match_by == 'rank':
                    if rank_match:
                        return True
                elif match_by == 'suit':
                    if suit_match:
                        return True
                elif match_by == 'rank_or_suit':
                    if rank_match or suit_match:
                        return True
                elif match_by == 'rank_and_suit':
                    if rank_match and suit_match:
                        return True

        return False

    @staticmethod
    def mark_all_table_cards_for_scoring(game_id, player_email):
        table_cards = TableCardRepository.get_table_cards(game_id)
        player = UserRepository.get_user_by_email(player_email)
        for card in table_cards:
            ValidCardRepository.create_valid_card(player.id, game_id, card.id, CardTypeEnum.TABLE_CARD)

    @staticmethod
    def remove_table_cards(game_id):
        ValidCardRepository.remove_valid_cards(game_id)
        TableCardRepository.delete_all_by_game_id(game_id)

    @staticmethod
    def player_has_matching_cards(game_id, player_email, match_by):
        player = UserRepository.get_user_by_email(player_email)
        player_cards = PlayerCardRepository.get_player_cards(game_id, player.id)

        matching_cards = []

        for i in range(len(player_cards)):
            for j in range(i + 1, len(player_cards)):
                card1 = player_cards[i]
                card2 = player_cards[j]

                rank_match = card1.card.rank == card2.card.rank
                suit_match = card1.card.suit == card2.card.suit

                if match_by == 'rank':
                    match = rank_match
                elif match_by == 'suit':
                    match = suit_match
                elif match_by == 'rank_or_suit':
                    match = rank_match or suit_match
                elif match_by == 'rank_and_suit':
                    match = rank_match and suit_match
                else:
                    match = False

                if match:
                    if player_cards[i] not in matching_cards:
                        matching_cards.append(player_cards[i])
                    if player_cards[j] not in matching_cards:
                        matching_cards.append(player_cards[j])

        matching_cards_dicts = []
        for card in matching_cards:
            card_dict = {
                "id": card.id,
                "rank": card.card.rank,
                "suit": card.card.suit,
                "card_type": CardTypeEnum.PLAYER_CARD
            }
            matching_cards_dicts.append(card_dict)

        return matching_cards_dicts

    @staticmethod
    def mark_matching_cards_valid(game_id, player_email, cards):
        player = UserRepository.get_user_by_email(player_email)
        for card in cards:
            if isinstance(card, dict):
                card_type = CardTypeEnum(card["card_type"])
                card_id = card["id"]
            else:
                card_type = card.card_type
                card_id = card.id

            ValidCardRepository.create_valid_card(player.id, game_id, card_id, card_type)

    @staticmethod
    def current_player_min_has_cards(game_id, player_email, number):
        player = UserRepository.get_user_by_email(player_email)
        cards = PlayerCardRepository.get_player_cards(game_id, player.id)
        return len(cards) >= number

    @staticmethod
    def remove_players_cards(game_id):
        PlayerCardRepository.delete_players_cards(game_id)

    @staticmethod
    def exchange_cards(exchange_buffer):
        for game_id, players in exchange_buffer.items():
            for player_email, cards in players.items():
                for card in cards:
                    card_from_db = CardRepository.get(game_id, card['rank'], card['suit'])
                    PlayerCardRepository.delete_player_card_by_id(card['id'])

                    rival_email = next((email for game_id, players in exchange_buffer.items()
                                        for email in players if email != player_email), None)
                    rival = UserRepository.get_user_by_email(rival_email)
                    PlayerCardRepository.create_player_card(game_id, rival.id, card_from_db.id)

    @staticmethod
    def reveal_selected_cards(cards):
        for card in cards:
            TableCardRepository.update_table_card_visibility(card['id'], True)

    @staticmethod
    def selected_cards_match(cards, match_by):
        if not cards:
            return []

        first_card = cards[0]

        if match_by == "rank":
            if all(card['rank'] == first_card['rank'] for card in cards):
                return cards

        elif match_by == "suit":
            if all(card['suit'] == first_card['suit'] for card in cards):
                return cards

        elif match_by == "rank_and_suit":
            if all(card['rank'] == first_card['rank'] and card['suit'] == first_card['suit'] for card in cards):
                return cards

        elif match_by == "rank_or_suit":
            all_same_rank = all(card['rank'] == first_card['rank'] for card in cards)
            all_same_suit = all(card['suit'] == first_card['suit'] for card in cards)
            if all_same_rank or all_same_suit:
                return cards

        return []

    @staticmethod
    def reset_table_cards_visibility(game_id, visibility):
        table_cards = TableCardRepository.get_table_cards(game_id)
        for card in table_cards:
            TableCardRepository.update_table_card_visibility(card.id, visibility)



