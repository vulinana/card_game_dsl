const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socket = io.connect(protocol + '//' + document.domain + ':' + location.port);

window.addEventListener('beforeunload', function (event) {
  event.preventDefault()
});

document.addEventListener('DOMContentLoaded', () => {
    var selected_player_card = null;
    var selected_table_cards = [];
    var selected_game = null;

    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('connect_and_load_game_names', localStorage.getItem('email'));
    });

    socket.on('game_names_loaded', data => {
        const gameList = document.getElementById('game-list');
        gameList.innerHTML = '';

        data.game_names.forEach((name, index) => {
            const button = document.createElement('button');
            button.textContent = name;
            button.className = 'game-button';
            button.onclick = () => {
                selected_game = name;
                const allButtons = document.querySelectorAll('.game-button');
                allButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.toggle('active');
                socket.emit('load_game_by_name', name);
            };
            if (index === 0) {
                button.classList.add('active');
                selected_game = name
            }
            gameList.appendChild(button);
        });

        socket.emit('load_logged_users')
    });

    socket.on('logged_users_loaded', data => {
        const playground = document.getElementById('playground');
        playground.innerHTML = '';
        console.log(data.game)

        const player_buttons = document.createElement('div');
        const title = document.createElement('span')
        title.textContent = 'Pick active player:'
        player_buttons.appendChild(title)

        player_buttons.className = 'player-buttons'
        playground.appendChild(player_buttons)

        data.users.forEach(user => {
            const button = document.createElement('button');
            button.textContent = user;
            button.className = 'player-button';
            button.onclick = () => {
                socket.emit('player_picked', user, selected_game)
            };
            player_buttons.appendChild(button);
        });
    });

    socket.on('game_invitation', (data) => {
        if (confirm(`Do you want to play ${data.game_name} with ${data.rival}?`)) {
            console.log("accept_invitation")
            socket.emit('accept_invitation', data.rival, data.game_name);
        } else {
            socket.emit('decline_invitation', { game_name: gameName });
        }
    });

     socket.on('loaded_game_by_name', (data) => {
        console.log("loaded_game_by_name ", data)
        displayPlayerCards(data.player_cards, 'top', data.rival)
        displayTableCards(data.table_cards)
        displayPlayerCards(data.player_cards, 'bottom', "You")
    });

    function displayTableCards(cards) {
        const playground = document.getElementById('playground');

        const playerButtons = document.querySelector('.player-buttons');
        if (playerButtons) playerButtons.remove();

        const existingTableCards = document.querySelector('.table-cards');
        if (existingTableCards) existingTableCards.remove();

        const tableCardsContainer = document.createElement('div');
        tableCardsContainer.className = 'table-cards';

        cards.forEach(card => {
            console.log(card)
            const cardElement = document.createElement('img');
            cardElement.src = `static/imgs/${card.rank}_of_${card.suit}.png`;
            cardElement.alt = `${card.rank} of ${card.suit}`;
            cardElement.className = 'card-image';
            cardElement.style.cursor = 'pointer';
            cardElement.onclick = () => {
                if (cardElement.classList.contains('selected')) {
                    removeTableCard(card)
                    cardElement.classList.remove('selected');
                }
                else {
                    selected_table_cards.push(card)
                    cardElement.classList.add('selected');
                }
            };

            tableCardsContainer.appendChild(cardElement);
        });

        playground.appendChild(tableCardsContainer);
    }


    function displayPlayerCards(cards, position = 'top', player) {
        const playground = document.getElementById('playground');

        const playerFrame = document.createElement('div');
        playerFrame.classList.add('player-frame');

        const nameLabel = document.createElement('span');
        nameLabel.textContent = `${player}: ${0}`;
        nameLabel.className = 'name-label'

        const cardsFrame = document.createElement('div');
        cardsFrame.className = 'cards-frame'

        cards.forEach(card => {
            const cardElement = document.createElement('img');
            cardElement.className = 'card-image';

            if (position === 'bottom') {
                cardElement.src = `/static/imgs/${card.rank}_of_${card.suit}.png`;
                cardElement.style.cursor = 'pointer';
            } else {
                cardElement.src = '/static/imgs/card_background.png';
            }

            if (position === 'bottom') {
                cardElement.onclick = () => {
                    selected_player_card = card

                    const selectedCards = document.querySelectorAll('.card-image.selected-player-card');
                    selectedCards.forEach(el => el.classList.remove('selected-player-card'));

                    cardElement.classList.toggle('selected-player-card');
                };
            }
            cardsFrame.appendChild(cardElement);
        });

        if (position === 'top') {
            playerFrame.appendChild(nameLabel);
            playerFrame.appendChild(cardsFrame)
        } else {
            playerFrame.appendChild(cardsFrame)
            playerFrame.appendChild(nameLabel);
        }

        playground.appendChild(playerFrame);
    }

    function removeTableCard(card) {
        const index = selected_table_cards.findIndex(c => c.rank === card.rank && c.suit === card.suit);

        if (index !== -1) {
            selected_table_cards.splice(index, 1);
        }
    }

    document.getElementById('next-round-button').addEventListener('click', () => {
        socket.emit('next_round');
    });

    socket.on('new_round', data => {
        console.log(`New round: ${data.round}`);
    });

    socket.on('update_score', data => {
        document.getElementById('player-score').textContent = data.player_points[0];
    });
});

function logout() {
    socket.emit('logout')

    socket.on('successful_logout', data => {
         window.location.href = '/'
    });
}