from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
from gme.services.game_service import GameService
from gme.utils import load_games_shared
from extensions import socketio

gme_routes = Blueprint('gme', __name__, static_folder='static', template_folder='templates')

card_games = []
connected_users = {}
games = {}

def get_connected_user_sid(email):
    return next((k for k, v in connected_users.items() if v == email), None)

def get_connected_user_email(sid):
    return connected_users.get(sid)


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

    user = GameService.get_user_by_email_and_password(email, password)

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
        send_invitation_to = get_connected_user_sid(email)
        rival = get_connected_user_email(request.sid)
        emit('game_invitation', {'game_name': game_name, 'rival': rival}, to=send_invitation_to)
    else:
        emit('error', {'message': f"Player with email {email} is not connected."})

@socketio.on('accept_invitation')
def accept_invitation(rival_email, game_name):
    if rival_email in connected_users.values():
        player2_sid = get_connected_user_sid(rival_email)
        player1_email = get_connected_user_email(request.sid)
        game = next((game for game in load_games_shared() if game.name == game_name), None)

        table_cards, player1_cards, player2_cards, game_id = GameService.accept_invitation(player1_email, rival_email, game)

        emit('loaded_game_by_name',
                                {'rival': connected_users.get(player2_sid),
                                 'player_cards': [card.to_dict() for card in player1_cards],
                                 'table_cards': [card.to_dict() for card in table_cards],
                                 'game_id': game_id,
                                 'rival_cards_count': len(player2_cards),
                                 'player_points': 0,
                                 'rival_points': 0},
                                                                                            to=request.sid)
        emit('loaded_game_by_name',
                                 {'rival': connected_users.get(request.sid),
                                  'player_cards': [card.to_dict() for card in player2_cards],
                                  'table_cards': [card.to_dict() for card in table_cards],
                                  'game_id': game_id,
                                  'rival_cards_count': len(player1_cards),
                                  'player_points': 0,
                                  'rival_points': 0},
                                                                                            to=player2_sid)
    else:
        emit('loaded_game_by_name', {'error': 'Rival is no longer active'}, to=request.sid)

@socketio.on('decline_invitation')
def decline_invitation(rival_email, game_name):
    if rival_email in connected_users.values():
        player2_sid = get_connected_user_sid(rival_email)
        user_who_rejected = get_connected_user_email(request.sid)
        emit('invitation_declined', {'rival': user_who_rejected, 'game_name': game_name}, to=player2_sid)

@socketio.on('finish_move')
def finish_move(game_id, selected_table_cards, selected_player_card):
    player_email = get_connected_user_email(request.sid)
    table_cards, player1_cards, player2_cards, player1, player2, game_players, winner = GameService.finish_move(game_id, selected_table_cards, selected_player_card, player_email)
    player2_sid = get_connected_user_sid(player2.user.email)

    if winner is not None:
        winner_sid = get_connected_user_sid(winner.user.email)
        emit('game_over', {'message': 'You won!'}, to=winner_sid)
        losers = [p for p in game_players if p.user.email != winner.user.email]
        for loser in losers:
            loser_sid = get_connected_user_sid(loser.user.email)
            emit('game_over', {'message': 'You are loser :('}, to=loser_sid)

    emit('loaded_game_by_name',
         {'rival': player2.user.email,
          'player_cards': [card.to_dict() for card in player1_cards],
          'table_cards': [card.to_dict() for card in table_cards],
          'game_id': game_id,
          'rival_cards_count': len(player2_cards),
          'player_points': player1.points,
          'rival_points': player2.points},
         to=request.sid)

    emit('loaded_game_by_name',
         {'rival': player_email,
          'player_cards': [card.to_dict() for card in player2_cards],
          'table_cards': [card.to_dict() for card in table_cards],
          'game_id': game_id,
          'rival_cards_count': len(player1_cards),
          'player_points': player2.points,
          'rival_points': player1.points},
         to=player2_sid)
@socketio.on('is_player_turn')
def is_player_turn(game_id):
    game = GameService.get_game(game_id)
    player_email = get_connected_user_email(request.sid)
    is_turn = game.current_player.email == player_email
    emit('player_turn_status', {'is_turn': is_turn}, room=request.sid)



