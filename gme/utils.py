import os
from textx import metamodel_from_file
from gme.model.card_game import CardGame
import random
from itertools import combinations
import bcrypt

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def module_path(relative_path):
    return os.path.join(os.path.dirname(__file__), relative_path)

entity_mm = metamodel_from_file(module_path('grammar.tx'))

def scan_game_files():
    game_files = []
    for file in os.listdir(module_path("games")):
        if file.endswith(".gme"):
            game_files.append(os.path.join(module_path("games"), file))
    return game_files

def load_game_model(file_path):
    model = entity_mm.model_from_file(file_path)
    return CardGame(model)

def load_games_shared():
    game_files = scan_game_files()
    return [load_game_model(file_path) for file_path in game_files]


def random_cards(card_count_list, number):
    selected_cards = []
    available_cards = [card for card in card_count_list if card.count > 0]

    while number > 0:
        if not available_cards:
            break

        available_cards = [card for card in card_count_list if card.count > 0]
        selected_card = random.choice(available_cards)
        selected_cards.append(selected_card.card)
        selected_card.count -= 1
        number -= 1

    return selected_cards, card_count_list

def get_valid_card_combinations_by_rank(selected_player_card, selected_table_cards):
    target_value = int(selected_player_card['rank'])

    valid_combinations = []
    invalid_cards = selected_table_cards.copy()  # Kopija originalnih karata

    # Prolazimo kroz sve moguće kombinacije
    for i in range(1, len(selected_table_cards) + 1):
        for combo in combinations(selected_table_cards, i):
            if sum(int(card['rank']) for card in combo) == target_value:
                valid_combinations.append(combo)

                # Uklanjamo karte koje su deo ove validne kombinacije
                for card in combo:
                    if card in invalid_cards:
                        invalid_cards.remove(card)

    valid_cards = [selected_player_card]
    for combo in valid_combinations:
        for card in combo:
            valid_cards.append(card)

    return valid_cards, invalid_cards




