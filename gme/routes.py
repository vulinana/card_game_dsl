from flask import Blueprint, render_template, request, jsonify, send_file
from flask_socketio import emit

from gme.services.game_service import GameService
from gme.services.state_service import StateService
from gme.services.user_service import UserService
from gme.utils import load_games_shared, try_parse_int
from extensions import socketio
from models import GameRequestStatus
from graphviz import Digraph

gme_routes = Blueprint('gme', __name__, static_folder='static', template_folder='templates')

card_games = []
connected_users = {}
games = {}
exchange_buffer = {}


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
    message, status = UserService.get_user_by_email_and_password(email, password)
    return jsonify({'email': email, 'message': message}), status


@gme_routes.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    message, status = UserService.create_user(username, email, password)

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
            'min_number_of_players': game.rules.min_players,
            'max_number_of_players': game.rules.max_players
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
            emit('game_invitation', {'game_name': game_name, 'rival': game_initiator, 'game_id': new_game.id},
                 to=send_invitation_to)
        else:
            emit('error', {'message': f"Player with email {email} is not connected."})


@socketio.on('accept_invitation')
def accept_invitation(rival_email, game_id):
    player_email = get_connected_user_email(request.sid)
    print("accept invitation")
    player_from_db = UserService.get_user(player_email)
    GameService.update_game_request_status(game_id, player_from_db.id, GameRequestStatus.ACCEPTED)

    game_from_db = GameService.get_game(game_id)
    game_initiator_sid = get_connected_user_sid(game_from_db.game_initiator.email)
    if (any(request.status == GameRequestStatus.PENDING for request in game_from_db.game_requests)):
        emit('invitation_resolved', {'message': f"Player {player_email} accepted invitation. Waiting for others!"},
             to=game_initiator_sid)
        emit('invitation_resolved', {
            'message': f"Player {game_from_db.game_initiator.email} is happy you want to play. Waiting for others to accept!"},
             to=request.sid)

    else:
        GameService.create_game_players(game_id)
        play_game(game_id)


@socketio.on('decline_invitation')
def decline_invitation(game_id):
    player_email = get_connected_user_email(request.sid)
    player_from_db = UserService.get_user(player_email)
    GameService.update_game_request_status(game_id, player_from_db.id, GameRequestStatus.DECLINED)

    game_from_db = GameService.get_game(game_id)
    game_initiator_sid = get_connected_user_sid(game_from_db.game_initiator.email)

    has_pending_requests = any(gr.status == GameRequestStatus.PENDING for gr in game_from_db.game_requests)
    accepted_game_requests = [gr for gr in game_from_db.game_requests if gr.status == GameRequestStatus.ACCEPTED]

    if not has_pending_requests and len(accepted_game_requests) + 1 < game_from_db.min_number_of_players:
        emit('notification', {
            'message': f"Player {player_email} declined invitation to play {game_from_db.name}. Not enough players :("},
             to=game_initiator_sid)
        for game_request in accepted_game_requests:
            user_sid = get_connected_user_sid(game_request.user.email)
            emit('notification', {'message': "Not enough players :("}, to=user_sid)
    elif has_pending_requests:
        emit('invitation_resolved',
             {'message': f"Player {player_email} declined invitation to play {game_from_db.name}."},
             to=game_initiator_sid)
    else:
        play_game(game_id)


@socketio.on('play_game')
def play_game(game_id, selected_player_cards = [], selected_table_cards = [], matching_cards = [], selected_user = None, new_round = False):
    print("play game ", game_id)
    game_from_db = GameService.get_game(game_id)
    game = next((game for game in load_games_shared() if game.name == game_from_db.name), None)

    if len(game_from_db.next_states) != 1:
        print("game over or player's decision")
        return

    current_state = next((state for state in game.states if state.name == game_from_db.next_states[0]), None)

    action = current_state.action
    condition = None
    match action.name:
        case 'deal_table_cards':
            print("case deal table cards")
            StateService.deal_table_cards(action.params[0], game, game_id)
            display_table_cards(game_id, game.rules)
            display_player_cards(game_id, game.rules.rounds)
        case 'deal_player_cards':
            print("case deal player cards")
            StateService.deal_player_cards(action.params[0], game_id)
            display_table_cards(game_id, game.rules)
            display_player_cards(game_id, game.rules.rounds)
        case 'fill_player_hand_to':
            StateService.fill_player_hand_to(game_id, action.params[0])
            display_player_cards(game_id, game.rules.rounds)
        case 'next_player':
            print("case next player")
            next_player_email = StateService.next_player(game_id, new_round, game.rules.next_player_in_round_condition)
            for player in GameService.get_game_players(game_id):
                player_sid = get_connected_user_sid(player.user.email)
                is_turn = next_player_email == player.user.email
                emit('player_turn_status', {'is_turn': is_turn}, to=player_sid)
        case 'throw_cards':
            print("case throw cards")
            if len(selected_player_cards) == 0:
                return
            StateService.throw_cards(game_id, selected_player_cards[0])
            selected_player_cards = []
            display_table_cards(game_id, game.rules)
            display_player_cards(game_id, game.rules.rounds)
        case 'check_if_any_players_cards':
            print("case check_if_any_players_cards")
            condition = StateService.check_if_any_players_cards(game_id)
        case 'select_player_cards_and_table_cards':
            if len(selected_player_cards) == 0 or len(selected_table_cards) == 0:
                return
            print("case select player cards and table cards")
        case 'select_table_cards':
            print("case select_table_cards")
            if len(selected_table_cards) == 0:
                return
        case 'cards_selection_sum_matching':
            print("case cards_selection_sum_matching")
            matching_cards = StateService.cards_selection_sum_matching(selected_player_cards[0], selected_table_cards)
            condition = len(matching_cards) != 0
            selected_player_cards = []
            selected_table_cards = []
        case 'calculate_points':
            print("case calculate points for current player")
            StateService.calculate_points(game_id)
            display_points(game_id)
        case 'remove_selected_cards':
            print("case remove selected cards")
            StateService.remove_selected_cards(game_id)
            display_table_cards(game_id, game.rules)
            display_player_cards(game_id, game.rules.rounds)
        case 'notify_player_of_invalid_move':
            emit('toastr', {'message': "Invalid move"}, to=request.sid)
        case 'new_round':
            StateService.new_round(game_id)
            new_round = True
        case 'check_if_rounds_remaining':
            condition = StateService.check_if_rounds_remaining(game_id, game.rules.rounds)
        case 'determine_game_winner':
            winners = StateService.determine_game_winner(game_id, game.rules.game_winner)
            display_winners(game_id, winners)
        case 'any_matching_table_cards':
            print("case any_matching_table_cards")
            condition = StateService.any_matching_table_cards(game_id, action.params[0])
        case 'mark_all_table_cards_for_scoring':
            print("case mark_table_cards_for_scoring")
            player_email = get_connected_user_email(request.sid)
            condition = StateService.mark_all_table_cards_for_scoring(game_id, player_email)
        case 'remove_table_cards':
            StateService.remove_table_cards(game_id)
            display_table_cards(game_id, game.rules)
        case 'player_has_matching_cards':
            player_email = get_connected_user_email(request.sid)
            matching_cards = StateService.player_has_matching_cards(game_id, player_email, action.params[0])
            condition = len(matching_cards) != 0
        case 'mark_matching_cards_for_scoring':
            player_email = get_connected_user_email(request.sid)
            StateService.mark_matching_cards_valid(game_id, player_email, matching_cards)
            matching_cards = []
        case 'current_player_min_has_cards':
            print("case current_player_min_has_cards")
            player_email = get_connected_user_email(request.sid)
            condition = StateService.current_player_min_has_cards(game_id, player_email, action.params[0])
        case 'remove_players_cards':
            StateService.remove_players_cards(game_id)
        case 'exchange_cards':
            player_email = get_connected_user_email(request.sid)
            if game_id not in exchange_buffer:
                exchange_buffer[game_id] = {player_email: []}
                players = GameService.get_game_players(game_id)
                other_players = [p.user.email for p in players if p.user.email != player_email]
                emit('choose_player_to_exchange', {'players': other_players, 'numberOfCards': action.params[0]}, to=request.sid)
                return
            else:
                if len(selected_player_cards) == 0:
                    exchange_buffer[game_id][selected_user] = []
                    player_emails = list(exchange_buffer[game_id].keys())
                    for email in player_emails:
                        player_sid = get_connected_user_sid(email)
                        emit('player_turn_status', {'is_turn': True, 'maxPlayersCardsSelectable': action.params[0]}, to=player_sid)
                    return
                else:
                    exchange_buffer[game_id][player_email] = selected_player_cards
                    if any(len(cards) == 0 for cards in exchange_buffer[game_id].values()):
                        emit('waiting', to=request.sid)
                        return
                    else:
                        StateService.exchange_cards(exchange_buffer)
                        del exchange_buffer[game_id]
                        display_player_cards(game_id, game.rules.rounds)
        case 'reveal_selected_cards':
            print("case reveal_selected_cards")
            if len(selected_table_cards) + len(selected_player_cards) == 0:
                return
            StateService.reveal_selected_cards(selected_table_cards + selected_player_cards)
            display_table_cards(game_id, game.rules)
            socketio.sleep(2)
        case 'selected_cards_match':
            print("case selected_cards_match")
            matching_cards = StateService.selected_cards_match(selected_player_cards + selected_table_cards, action.params[0])
            condition = len(matching_cards) != 0
            selected_player_cards = []
            selected_table_cards = []
        case 'reset_table_cards_visibility':
            StateService.reset_table_cards_visibility(game_id, game.rules.table_cards_visible)
            display_table_cards(game_id, game.rules)
        case _:
            print(f"Unknown game action: {action.name}")
            return

    GameService.find_next_states(game_id, current_state, condition)
    play_game(game_id, selected_player_cards, selected_table_cards, matching_cards, None, new_round)


def display_table_cards(game_id, rules):
    table_cards = GameService.get_table_cards(game_id)
    round = GameService.get_current_round(game_id)
    for player in GameService.get_game_players(game_id):
        player_sid = get_connected_user_sid(player.user.email)
        emit('display_table_cards', {
            'game_id': game_id,
            'cards': table_cards,
            'round': f'{round.number}/{rules.rounds}'
        },
             to=player_sid)

def display_points(game_id):
    game_players = GameService.get_game_players(game_id)
    for player in game_players:
        player_sid = get_connected_user_sid(player.user.email)
        emit('set_points', {
            'game_players': [player.to_dict() for player in game_players],
        },
             to=player_sid)


def display_player_cards(game_id, max_rounds):
    player_cards = GameService.get_players_cards_data(game_id)
    round = GameService.get_current_round(game_id)
    for player in player_cards:
        player_sid = get_connected_user_sid(player.get("player_email"))
        rivals = [player_cards for player_cards in player_cards if
                  player_cards["player_email"] != player.get("player_email")]
        emit('display_player_cards', {
            'player': player,
            'rivals': rivals,
            'game_id': game_id,
            'round': f'{round.number}/{max_rounds}'
        },
             to=player_sid)

def display_winners(game_id, winners):
    if len(winners) > 1:
        for w in winners:
            winner_sid = get_connected_user_sid(w.user.email)
            emit('game_over', {'message': 'No one won! You have the same score.'}, to=winner_sid)
    else:
        winner_sid = get_connected_user_sid(winners[0].user.email)
        emit('game_over', {'message': 'You won!'}, to=winner_sid)

        losers = [player.user.email for player in GameService.get_game_players(game_id) if
                  player.user.email != winners[0].user.email]
        for loser in losers:
            loser_sid = get_connected_user_sid(loser)
            emit('game_over', {'message': 'You are loser :('}, to=loser_sid)


@socketio.on('finish_move')
def finish_move(game_id, selected_table_cards, selected_player_cards):
    game_from_db = GameService.get_game(game_id)
    game = next((game for game in load_games_shared() if game.name == game_from_db.name), None)

    if selected_player_cards and not selected_table_cards:
        player_action = 'throw_cards'
    if selected_table_cards and not selected_player_cards:
        player_action = 'select_table_cards'
    elif selected_player_cards and selected_table_cards:
        player_action = 'select_player_cards_and_table_cards'

    for next_state_name in game_from_db.next_states:
        next_state = next((state for state in game.states if state.name == next_state_name), None)
        if next_state.action.name == 'exchange_cards':
            max_hand_cards_selected = try_parse_int(
                next_state.action.params[0]) if next_state.action.params else None
            if len(selected_player_cards) != max_hand_cards_selected:
                emit('toastr', {'message': 'Select ' + str(max_hand_cards_selected) + ' cards for exchange'},
                     to=request.sid)
                return
            play_game(game_id, selected_player_cards, selected_table_cards)
            return

        if next_state.action.name == player_action:
            if player_action == 'throw_cards':
                max_hand_cards_selected = try_parse_int(
                    next_state.action.params[0]) if next_state.action.params else None
                if max_hand_cards_selected is not None and max_hand_cards_selected != len(selected_player_cards):
                    card_word = 'card' if max_hand_cards_selected == 1 else 'cards'
                    emit('toastr', {'message': f'You can throw {max_hand_cards_selected} {card_word}'}, to=request.sid)
                    return
            if player_action == 'select_table_cards':
                max_table_cards_selected = try_parse_int(
                    next_state.action.params[0]) if next_state.action.params else None
                if max_table_cards_selected is not None and max_table_cards_selected != len(selected_table_cards):
                    card_word = 'card' if max_table_cards_selected == 1 else 'cards'
                    emit('toastr', {'message': f'You can select {max_table_cards_selected} table {card_word}'}, to=request.sid)
                    return

            if player_action == 'select_player_cards_and_table_cards':
                max_hand_cards_selected = try_parse_int(
                    next_state.action.params[0]) if next_state.action.params else None
                max_table_cards_selected = try_parse_int(
                    next_state.action.params[1]) if next_state.action.params else None

                if max_hand_cards_selected is not None and max_hand_cards_selected != len(selected_player_cards):
                    card_word = 'card' if max_hand_cards_selected == 1 else 'cards'
                    emit('toastr', {'message': f'You can select {max_hand_cards_selected} hand {card_word}'}, to=request.sid)
                    return
                if max_table_cards_selected is not None and max_table_cards_selected != len(selected_table_cards):
                    card_word = 'card' if max_table_cards_selected == 1 else 'cards'
                    emit('toastr', {'message': f'You can select {max_hand_cards_selected} table {card_word}'}, to=request.sid)
                    return

            GameService.update_next_states(game_id, [next_state.name])
            play_game(game_id, selected_player_cards, selected_table_cards)

@socketio.on("user_selected")
def user_selected(game_id, selected_user):
    play_game(game_id, [], [], [], selected_user)


@socketio.on('game_rules')
def get_game_rules(game_name):
    game = next((game for game in load_games_shared() if game_name == game.name), None)
    text = f"{game.name}<br><br>"
    text += game.rules.to_text()

    dot = Digraph(comment='Card Game State Machine')
    dot.attr(rankdir='TB')
    dot.attr('node', style='filled', fontname='Helvetica', shape='box', fillcolor='lightblue')

    for state in game.states:
        params = ', '.join(str(p) for p in state.action.params)
        action_label = f"{state.action.name}({params})" if params else state.action.name
        label = f"{state.name}\n[do: {action_label}]"
        dot.node(state.name, label=label)

    for state in game.states:
        for transition in state.transitions:
            label = ''
            if transition.condition is not None:
                label = f"if {transition.condition}".lower()
            color = 'black'
            if str(transition.condition).lower() == 'false':
                color = 'red'
            elif str(transition.condition).lower() == 'true':
                color = 'green'
            dot.edge(state.name, transition.nextState, label=label, color=color)

    output_path = f'static/game_photos/{game.name}'
    dot.format = 'png'
    dot.render(output_path, cleanup=True)

    image_url = f"/static/game_photos/{game.name}.png"

    emit('game_rules', {
        'rules': text,
        'image_url': image_url
    }, to=request.sid)



