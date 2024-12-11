const apiUrl = window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8080'
    : 'https://web-production-84691.up.railway.app';
const socket = io.connect(apiUrl);
//const socket = io.connect(protocol + '//' + document.domain + ':' + location.port);

window.addEventListener('beforeunload', function (event) {
  event.preventDefault()
});

var selected_player_card = null;
var selected_table_cards = [];
var selected_game = null;
var game_id = null

document.addEventListener('DOMContentLoaded', () => {
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
                //const allButtons = document.querySelectorAll('.game-button');
                //allButtons.forEach(btn => btn.classList.remove('active'));
                //button.classList.toggle('active');
                //socket.emit('load_game_by_name', name);
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
        console.log("game invitation")
        if (confirm(`Do you want to play ${data.game_name} with ${data.rival}?`)) {
            console.log("accept_invitation")
            socket.emit('accept_invitation', data.rival, data.game_name);
        } else {
            socket.emit('decline_invitation', data.rival, data.game_name);
        }
    });

    socket.on('invitation_declined', (data) => {
        alert(`Player ${data.rival} rejected your invitation to play ${data.game_name}`)
    });

     socket.on('loaded_game_by_name', (data) => {
        const playground = document.getElementById('playground');
        playground.innerHTML = ''

        game_id = data.game_id
        displayRivalCards(data.rival_cards_count, data.rival, data.rival_points)
        displayTableCards(data.table_cards)
        displayPlayerCards(data.player_cards, data.player_points)
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
            const cardElement = document.createElement('img');
            cardElement.src = `static/imgs/${card.rank}_of_${card.suit}.png`;
            cardElement.alt = `${card.rank} of ${card.suit}`;
            cardElement.className = 'card-image';
            cardElement.style.cursor = 'not-allowed';
            cardElement.dataset.rank = card.rank;
            cardElement.dataset.suit = card.suit;

            tableCardsContainer.appendChild(cardElement);
        });

        playground.appendChild(tableCardsContainer);

        socket.emit('is_player_turn', game_id);
        socket.on('player_turn_status', (data) => {
            const isTurn = data.is_turn;
            const cardElements = document.querySelectorAll('.card-image');

            cardElements.forEach(card => {
                if (isTurn) {
                    card.style.cursor = 'pointer';
                    card.onclick = () => {
                        const rank = card.dataset.rank
                        const suit = card.dataset.suit
                        if (card.classList.contains('selected')) {
                            removeTableCard({'rank': rank, 'suit': suit})
                            card.classList.remove('selected');
                        }
                        else {
                            selected_table_cards.push({'rank': rank, 'suit': suit})
                            card.classList.add('selected');
                        }
                    };
                } else {
                    card.style.cursor = 'not-allowed';
                    card.onclick = null;
                }
            });
        });


     }

     function displayRivalCards(numberOfCards, player, points) {
        const playground = document.getElementById('playground');

        const playerFrame = document.createElement('div');
        playerFrame.classList.add('player-frame');

        const nameLabel = document.createElement('span');
        nameLabel.textContent = `${player}: ${points}`;
        nameLabel.className = 'name-label';

        const cardsFrame = document.createElement('div');
        cardsFrame.className = 'cards-frame';

        for (let i = 0; i < numberOfCards; i++) {
            const cardElement = document.createElement('img');
            cardElement.className = 'card-image';
            cardElement.src = '/static/imgs/card_background.png';

            cardsFrame.appendChild(cardElement);
        }

        playerFrame.appendChild(nameLabel);
        playerFrame.appendChild(cardsFrame);
        playground.appendChild(playerFrame);
    }

    function displayPlayerCards(cards, points, gameId) {
        const playground = document.getElementById('playground');

        const playerFrame = document.createElement('div');
        playerFrame.classList.add('player-frame');

        const nameLabel = document.createElement('span');
        nameLabel.textContent = `You: ${points}`;
        nameLabel.className = 'name-label';

        const cardsFrame = document.createElement('div');
        cardsFrame.className = 'cards-frame';

        cards.forEach(card => {
            const cardElement = document.createElement('img');
            cardElement.className = 'player-card-image';
            cardElement.src = `/static/imgs/${card.rank}_of_${card.suit}.png`;
            cardElement.style.cursor = 'not-allowed';
            cardElement.dataset.rank = card.rank;
            cardElement.dataset.suit = card.suit;

            cardsFrame.appendChild(cardElement);
        });

        playerFrame.appendChild(cardsFrame);
        playerFrame.appendChild(nameLabel);
        playground.appendChild(playerFrame);

        socket.emit('is_player_turn', game_id);
        socket.on('player_turn_status', (data) => {
            const isTurn = data.is_turn;
            const cardElements = document.querySelectorAll('.player-card-image');

            cardElements.forEach(card => {
                if (isTurn) {
                    card.style.cursor = 'pointer';
                    card.onclick = () => {
                        const rank = card.dataset.rank;
                        const suit = card.dataset.suit;
                        selected_player_card = {'rank': rank, 'suit': suit};

                        const selectedCards = document.querySelectorAll('.player-card-image.selected-player-card');
                        selectedCards.forEach(el => el.classList.remove('selected-player-card'));

                        card.classList.toggle('selected-player-card');
                    };
                } else {
                    card.style.cursor = 'not-allowed';
                    card.onclick = null;
                }
            });
        });
    }

    function removeTableCard(card) {
        const index = selected_table_cards.findIndex(c => c.rank === card.rank && c.suit === card.suit);

        if (index !== -1) {
            selected_table_cards.splice(index, 1);
        }
    }
});


function logout() {
    socket.emit('logout')

    socket.on('successful_logout', data => {
         window.location.href = '/'
    });
}

 function finishMove() {
    /*const totalTableValue = selected_table_cards.reduce((sum, card) => sum + parseInt(card.rank, 10), 0);
    const rankValue = parseInt(selected_player_card.rank, 10);
    if (!isNaN(rankValue) && rankValue === totalTableValue) {
        player_points += check_card_points(selected_player_card)
        selected_table_cards.forEach((card) => {
             player_points += check_card_points(card)
        });

        console.log(player_points)*/
      socket.emit('finish_move', game_id, selected_table_cards, selected_player_card)
 }

  function check_card_points(card) {
    if (card.rank == '10' && card.suit == 'diamonds')
        return 2
    if (card.rank == '10' || card.rank == 'A' || card.rank == '12' || card.rank == '13' || card.rank == '14' || (
            card.rank == '2' && card.suit == 'clubs'))
        return 1
  }
