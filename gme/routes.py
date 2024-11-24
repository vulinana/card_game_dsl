from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
from gme.game_logic.model.card import Card
from gme.game_logic.game import Game
from gme.utils import load_games_shared, random_cards
from extensions import socketio
from models import User

gme_routes = Blueprint('gme', __name__, static_folder='static', template_folder='templates')

card_games = []
game_instance = Game()
connected_users = {}

@gme_routes.route('/')
def render_login():
    return render_template('login.html', games=card_games)

@gme_routes.route('/index')
def render_index():
    return render_template('index.html', games=card_games)


#API routes
@gme_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password).first()

    if user:
        return jsonify({'email': user.email, 'message': 'Login successful'}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@socketio.on('logout')
def logout():
    if request.sid in connected_users.keys():
        del connected_users[request.sid]
    emit('successful_logout')

# SocketIO događaji
@socketio.on('connect_and_load_game_names')
def connect_and_load_game_names(email):
    for key, item in connected_users.items():
        if item == email:
            del connected_users[key]
            break
    connected_users[request.sid] = email
    card_games = load_games_shared()
    game_names = [game.name for game in card_games]
    emit('game_names_loaded', {'game_names': game_names})

@socketio.on('load_logged_users')
def load_logged_users():
    email = connected_users.get(request.sid)
    users_copy = connected_users.copy()
    if email in users_copy.values():
        del users_copy[request.sid]
    emit('logged_users_loaded', {'users': list(users_copy.values())})

@socketio.on('player_picked')
def player_picked(email, game_name):
    if email in connected_users.values():
        send_invitation_to = next((k for k, v in connected_users.items() if v == email), None)
        rival = connected_users[request.sid]
        emit('game_invitation', {'game_name': game_name, 'rival': rival}, to=send_invitation_to)
    else:
        emit('error', {'message': f"Player with email {email} is not connected."})

@socketio.on('accept_invitation')
def player_picked(rival_email, game_name):
    if rival_email in connected_users.values():
        player2_sid = next((k for k, v in connected_users.items() if v == rival_email), None)
        game = next((game for game in load_games_shared() if game.name == game_name), None)

        [table_cards, cards_left] = random_cards(game.cards, game.rules.number_of_table_cards)
        [player1_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)
        [player2_cards, cards_left] = random_cards(cards_left, game.rules.number_of_cards_per_round)

        emit('loaded_game_by_name', {'rival': connected_users.get(player2_sid), 'player_cards': [card.to_dict() for card in player1_cards], 'table_cards': [card.to_dict() for card in table_cards]}, to=request.sid)
        emit('loaded_game_by_name', {'rival': connected_users.get(request.sid), 'player_cards': [card.to_dict() for card in player2_cards], 'table_cards': [card.to_dict() for card in table_cards]}, to=player2_sid)
    else:
        emit('loaded_game_by_name', {'error': 'Rival is no longer active'}, to={request.sid})



@socketio.on('load_game_by_name')
def load_game_by_name(name):
    game = next((game for game in load_games_shared() if game.name == name), None)
    if game is not None:
        emit('loaded_game_by_name', {'game': game.to_dict()})
    else:
        emit('loaded_game_by_name', {'error': 'Game not found'})

@socketio.on('play_card')
def play_card(data):
    card_data = data['card']
    selected_card = Card(card_data['rank'], card_data['suit'])
    game_instance.gui.selected_player_card = selected_card
    game_instance.validate_points()
    emit('update_score', {'player_points': game_instance.player_points})

@socketio.on('next_round')
def next_round():
    game_instance.next_round()
    emit('new_round', {'round': game_instance.round})

