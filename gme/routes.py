from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
from gme.services.game_service import GameService
from gme.utils import load_games_shared
from extensions import socketio
from models import GameRequestStatus

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

@gme_routes.route('/register')
def render_register():
    return render_template('register.html', games=card_games)


#API routes
@gme_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    message, status = GameService.get_user_by_email_and_password(email, password)
    return jsonify({'email': email, 'message': message}), status


@gme_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    message, status = GameService.create_user(username, email, password)

    return jsonify({'email': email, 'message': message}), status


@socketio.on('logout')
def logout():
    if request.sid in connected_users.keys():
        del connected_users[request.sid]
    emit('successful_logout')
    load_logged_users()

# SocketIO događaji
@socketio.on('connect_and_load_game_names')
def connect_and_load_game_names(email):
    for key, item in connected_users.items():
        if item == email:
            del connected_users[key]
            break
    connected_users[request.sid] = email
    card_games = load_games_shared()
    games = [
        {
            'name': game.name,
            'min_number_of_players': game.rules.min_number_of_players,
            'max_number_of_players': game.rules.max_number_of_players
        }
        for game in card_games
    ]
    emit('games_loaded', {'games': games})

@socketio.on('load_logged_users')
def load_logged_users():
    for key, item in connected_users.items():
        users_copy = connected_users.copy()
        del users_copy[key]
        emit('logged_users_loaded', {'users': list(users_copy.values())}, to=key)

@socketio.on('players_picked')
def players_picked(selected_rivals, game_name):
    game_initiator = get_connected_user_email(request.sid)
    new_game = GameService.create_game_init(game_name, game_initiator, selected_rivals)
    for email in selected_rivals:
        if email in connected_users.values():
            send_invitation_to = get_connected_user_sid(email)
            emit('game_invitation', {'game_name': game_name, 'rival': game_initiator, 'game_id': new_game.id}, to=send_invitation_to)
        else:
            emit('error', {'message': f"Player with email {email} is not connected."})

@socketio.on('accept_invitation')
def accept_invitation(rival_email, game_id):
    player_email = get_connected_user_email(request.sid)
    player_from_db = GameService.get_user(player_email)
    GameService.update_game_request_status(game_id, player_from_db.id, GameRequestStatus.ACCEPTED)

    game_from_db = GameService.get_game(game_id)
    game_initiator_sid = get_connected_user_sid(game_from_db.game_initiator.email)
    if (any(request.status == GameRequestStatus.PENDING for request in game_from_db.game_requests)):
        emit('invitation_resolved', {'message': f"Player {player_email} accepted invitation. Waiting for others!"},
             to=game_initiator_sid)
        emit('invitation_resolved', {'message': f"Player {game_from_db.game_initiator.email} is happy you want to play. Waiting for others to accept!"},
             to=request.sid)

    else:
        game = next((game for game in load_games_shared() if game.name == game_from_db.name), None)
        table_cards, player_cards_data = GameService.start_game(game_id, game)
        for player in player_cards_data:
            player_sid = get_connected_user_sid(player.get("player_email"))
            rivals = [player_cards for player_cards in player_cards_data if player_cards["player_email"] != player.get("player_email")]
            emit('loaded_game_by_name', {
                                            'table_cards': table_cards,
                                            'player': player,
                                            'rivals': rivals,
                                            'game_id': game_id
                                         },
                                                                        to=player_sid)
@socketio.on('decline_invitation')
def decline_invitation(game_id):
    player_email = get_connected_user_email(request.sid)
    player_from_db = GameService.get_user(player_email)
    GameService.update_game_request_status(game_id, player_from_db.id, GameRequestStatus.DECLINED)

    game_from_db = GameService.get_game(game_id)
    game_initiator_sid = get_connected_user_sid(game_from_db.game_initiator.email)

    emit('invitation_declined', {'rival': player_email, 'game_name': game_from_db.name}, to=game_initiator_sid)

@socketio.on('finish_move')
def finish_move(game_id, selected_table_cards, selected_player_card):
    player_email = get_connected_user_email(request.sid)
    table_cards, player_cards_data, winner = GameService.finish_move(game_id, selected_table_cards, selected_player_card, player_email)

    if winner is not None:
        winner_sid = get_connected_user_sid(winner.user.email)
        emit('game_over', {'message': 'You won!'}, to=winner_sid)
        losers = [player["player_email"] for player in player_cards_data if player["player_email"] != winner.user.email]
        for loser in losers:
            loser_sid = get_connected_user_sid(loser)
            emit('game_over', {'message': 'You are loser :('}, to=loser_sid)

    for player in player_cards_data:
        player_sid = get_connected_user_sid(player.get("player_email"))
        rivals = [player_cards for player_cards in player_cards_data if player_cards["player_email"] != player.get("player_email")]
        emit('loaded_game_by_name', {
            'table_cards': table_cards,
            'player': player,
            'rivals': rivals,
            'game_id': game_id
        },
             to=player_sid)
@socketio.on('is_player_turn')
def is_player_turn(game_id):
    game = GameService.get_game(game_id)
    player_email = get_connected_user_email(request.sid)
    is_turn = game.current_player.email == player_email
    emit('player_turn_status', {'is_turn': is_turn}, room=request.sid)



