import os
import jwt
import datetime
from flask import current_app
from textx import metamodel_from_file
from .game_logic.model.card_game import CardGame
import random
from itertools import combinations


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

def generate_token(user_email):
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token važi 1 sat
    token = jwt.encode(
        {'email': user_email, 'exp': expiration_time},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return token


def decode_token(token):
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload['email']
    except jwt.ExpiredSignatureError:
        return "Token je istekao"
    except jwt.InvalidTokenError:
        return "Nevalidan token"



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


def validate_points(selected_table_cards, selected_player_card):
    target_value = int(selected_player_card['rank'])

    valid_combinations = []
    for i in range(1, len(selected_table_cards) + 1):
        for combo in combinations(selected_table_cards, i):
            if sum(int(card['rank']) for card in combo) == target_value:
                valid_combinations.append(combo)

    if not valid_combinations:
        return 0

    # Računanje poena za sve validne kombinacije
    points = 0
    points += check_card_points(selected_player_card)
    for combo in valid_combinations:
        for card in combo:
            points += check_card_points(card)

    return points

def check_card_points(card):
    if card['rank'] == '10' and card['suit'] == 'diamonds':
        return 2
    if card['rank'] in {'10', 'A', '12', '13', '14'} or (
            card['rank'] == '2' and card['suit'] == 'clubs'):
        return 1

    return 0