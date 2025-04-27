const apiUrl = window.location.hostname === 'localhost'
    ? 'http://127.0.0.1:8080'
    : 'https://web-production-84691.up.railway.app';
const socket = io.connect(apiUrl);
//const socket = io.connect(protocol + '//' + document.domain + ':' + location.port);

window.addEventListener('beforeunload', function (event) {
  event.preventDefault()
});

var selectedPlayerCards = [];
var selected_table_cards = [];
var selected_game = null;
var game_id = null
var selected_rivals = []

document.addEventListener('DOMContentLoaded', () => {
    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('connect_and_load_game_names', localStorage.getItem('email'));
    });

    socket.on('games_loaded', data => {
        const gameList = document.getElementById('game-list');
        gameList.innerHTML = '';
        data.games.forEach((game, index) => {
            const button = document.createElement('button');
            button.textContent = game.name;
            button.className = 'game-button';
            button.onclick = () => {
                selected_game = game;
                title = document.getElementById('playground-game-title');
                if (title != null)
                    title.innerHTML = `Play ${selected_game.name}<br>Number of Players ${selected_game.min_number_of_players - 1}-${selected_game.max_number_of_players - 1}`
                const allButtons = document.querySelectorAll('.game-button');
                allButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.toggle('active');
            };
            if (index === 0) {
                button.classList.add('active');
                selected_game = game
            }
            gameList.appendChild(button);
        });

        socket.emit('load_logged_users')
    });

    socket.on('logged_users_loaded', data => {
        const playground = document.getElementById('playground');
        playground.innerHTML = '';

        const playground_buttons = document.createElement('div')
        playground_buttons.className = 'playground-buttons'
        const title = document.createElement('div')
        title.id = 'playground-game-title';
        title.style.textAlign = 'center';
        title.style.fontSize = '24px';
        title.style.marginBottom = '20px';
        title.innerHTML = `Play ${selected_game.name}<br>Number of Players ${selected_game.min_number_of_players - 1}-${selected_game.max_number_of_players - 1}`
        playground_buttons.appendChild(title)

        const player_buttons = document.createElement('div');
        player_buttons.className = 'player-buttons'

        data.users.forEach(user => {
            const button = document.createElement('button');
            button.textContent = user;
            button.className = 'player-button';
            button.onclick = () => {
                 if (button.classList.toggle('selected')) {
                    selected_rivals.push(user);
                } else {
                    selected_rivals = selected_rivals.filter(rival => rival !== user);
                }
            };
            player_buttons.appendChild(button);
        });

        const send_invitation_button = document.createElement('button');
        send_invitation_button.textContent = "Send invitations";
        send_invitation_button.className = 'player-button'
        send_invitation_button.onclick = () => {
            if (selected_rivals.length >= selected_game.min_number_of_players - 1 && selected_rivals.length <= selected_game.max_number_of_players - 1)
            {
                socket.emit('players_picked', selected_rivals, selected_game.name)
                showLoader()
            }
            else
            {
                showNotification(`Insufficient number of selected players. Min: ${selected_game.min_number_of_players - 1}; Max: ${selected_game.max_number_of_players - 1}`, 3000);
            }
        };

        playground_buttons.appendChild(player_buttons)
        playground_buttons.appendChild(send_invitation_button)
        playground.appendChild(playground_buttons)
    });

    socket.on('game_invitation', (data) => {
      showModal(
        `Do you want to play ${data.game_name} with ${data.rival}?`,
        () => {
          socket.emit('accept_invitation', data.rival, data.game_id);
        },
        () => {
          socket.emit('decline_invitation', data.game_id);
        }
      );
    });

    socket.on('invitation_resolved', (data) => {
        showLoader()
        showAlert(data.message, () => {});
    });

    socket.on('notification', (data) => {
        hideLoader()
        showAlert(data.message, () => {});
    });

    socket.on('toastr', (data) => {
        showNotification(data.message, 3000);
    });

     socket.on('choose_player_to_exchange', (data) => {
        const player_buttons = document.createElement('div');
        const title = document.createElement('div')
        title.id = 'playground-game-title';
        title.style.textAlign = 'center';
        title.style.fontSize = '12px';
        title.style.marginBottom = '5px';
        title.innerHTML = `Exchange ${data.numberOfCards} cards with:`
        player_buttons.appendChild(title)

        data.players.forEach(player => {
            const button = document.createElement('button');
            button.textContent = player;
            button.className = 'player-button';
            button.onclick = () => {
                document.querySelectorAll('.player-button.selected').forEach(btn => btn.classList.remove('selected'));
                selected_rivals = [];
                button.classList.add('selected');
                selected_rivals.push(player);
            };
            player_buttons.appendChild(button);
        });

        showAlert(player_buttons, () => {
            socket.emit('user_selected', game_id, selected_rivals[0])
        });
    });

    socket.on('waiting', () => {
        showLoader()
    });

    socket.on('set_points', (data) => {
        data.game_players.forEach((player, index) => {
            const nameLabel = document.getElementById(player.email)
            if (nameLabel) nameLabel.textContent = `${player.email}: ${player.points}`;
        });
    });

    function setRound(round) {
        const playground = document.getElementById('playground');
        const oldRoundText = document.getElementById('roundText')
        if (oldRoundText)
            oldRoundText.remove()

        const roundText = document.createElement('div');
        roundText.id = 'roundText'
        roundText.textContent = "Round " + round;
        roundText.style.position = 'absolute';
        roundText.style.top = '0';
        roundText.style.left = '0';
        roundText.style.padding = '10px';
        roundText.style.color = 'black';
        roundText.style.fontSize = '20px';
        playground.appendChild(roundText);
    }

    function clearPlayground(){
        hideLoader()
        const title = document.getElementById('playground-game-title')
        if (title) title.remove()
        const playerButtons = document.querySelector('.player-buttons');
        if (playerButtons) playerButtons.remove();
        const sendInvitationButton = document.querySelector('.player-button');
        if (sendInvitationButton) sendInvitationButton.remove();
    }

    function clearTableCards() {
        clearPlayground()
        const existingTableCards = document.querySelector('.table-cards');
        if (existingTableCards) existingTableCards.remove();
    }

    function clearPlayerCards() {
       clearPlayground()
       const existingPlayerCards = document.querySelectorAll('.player-frame');

        if (existingPlayerCards?.length > 0) {
            existingPlayerCards.forEach(el => el.innerHTML = '');
        }
    }

    socket.on('display_table_cards', (data) => {
        game_id = data.game_id
        selectedPlayerCards = []
        selected_table_cards = []
        clearTableCards()
        setRound(data.round)
        displayTableCards(data.cards);
    });


    socket.on('display_player_cards', (data) => {
        game_id = data.game_id
        selectedPlayerCards = []
        selected_table_cards = []
        clearPlayerCards()
        setRound(data.round)
        displayRivalCards(data.rivals);
        displayPlayerCards(data.player, data.player.points);
    });

    function displayRivalCards(rivals) {
        const playground = document.getElementById('playground');

        const playgroundWidth = playground.offsetWidth;
        const playgroundHeight = playground.offsetHeight;

        rivals.forEach((rival, index) => {
            const playerFrame = document.createElement('div');
            playerFrame.className = 'player-frame';
            playerFrame.style.position = 'absolute';

            const nameLabel = document.createElement('span');
            nameLabel.id = rival.player_email
            nameLabel.textContent = `${rival.player_email}: ${rival.points}`;
            nameLabel.className = 'name-label';

            const cardsFrame = document.createElement('div');
            cardsFrame.className = 'cards-frame';

            rival.cards.forEach(card => {
                const cardElement = document.createElement('img');
                cardElement.className = 'card-image';
                cardElement.src = '/static/imgs/card_background.png'; // Pozadina kartice
                cardsFrame.appendChild(cardElement);
            });

            playerFrame.appendChild(nameLabel);
            playerFrame.appendChild(cardsFrame);

            const playgroundHeight = playground.offsetHeight
            if (index === 0) {
                playerFrame.style.top = '10px';
            } else if (index === 1) {
                playerFrame.style.transform = 'rotate(90deg)';
                playerFrame.style.transformOrigin = 'center center';

                playerFrame.style.top = `${(playground.offsetHeight - playerFrame.offsetHeight)/3}px`;
                const frameWidth = playerFrame.offsetWidth;
                playerFrame.style.right = `0px`;
            } else {
                playerFrame.style.transform = 'rotate(-90deg)';
                playerFrame.style.transformOrigin = 'center center';

                playerFrame.style.top = `${(playground.offsetHeight - playerFrame.offsetHeight)/3}px`;
                const frameWidth = playerFrame.offsetWidth;
                playerFrame.style.left = `0px`;
            }

            playground.appendChild(playerFrame);
        });
    }


    function displayTableCards(cards) {
        const playground = document.getElementById('playground');

        const tableCardsContainer = document.createElement('div');
        tableCardsContainer.className = 'table-cards';

        cards.forEach(card => {
            const cardElement = document.createElement('img');
            if (card.visible)
                cardElement.src = `static/imgs/${card.rank}_of_${card.suit}.png`;
            else
                cardElement.src = '/static/imgs/card_background.png';
            cardElement.alt = `${card.rank} of ${card.suit}`;
            cardElement.className = 'card-image';
            cardElement.style.cursor = 'not-allowed';
            cardElement.dataset.id = card.id
            cardElement.dataset.rank = card.rank;
            cardElement.dataset.suit = card.suit;
            cardElement.dataset.cardType = card.card_type

            tableCardsContainer.appendChild(cardElement);
        });

        playground.appendChild(tableCardsContainer);
    }

    socket.on('player_turn_status', (data) => {
        console.log("player_turn_status", data.is_turn)
        const isTurn = data.is_turn;
        const cardElements = document.querySelectorAll('.card-image');

        cardElements.forEach(card => {
            if (isTurn) {
                card.style.cursor = 'pointer';
                card.onclick = () => {
                    const id = card.dataset.id
                    const rank = card.dataset.rank;
                    const suit = card.dataset.suit;
                    const cardType = card.dataset.cardType

                    if (card.classList.contains('selected')) {
                        removeTableCard({'id': id, 'rank': rank, 'suit': suit, 'card_type': cardType});
                        card.classList.remove('selected');
                    } else {
                        selected_table_cards.push({'id': id, 'rank': rank, 'suit': suit, 'card_type': cardType});
                        card.classList.add('selected');
                    }
                };
            } else {
                card.style.cursor = 'not-allowed';
                card.onclick = null;
            }
        });

        const playerCardElements = document.querySelectorAll('.player-card-image');
        playerCardElements.forEach(card => {
            if (isTurn) {
                card.style.cursor = 'pointer';
                card.onclick = () => {
                    const id = card.dataset.id;
                    const rank = card.dataset.rank;
                    const suit = card.dataset.suit;
                    const cardType = card.dataset.cardType
                    if (card.classList.contains('selected-player-card')) {
                        card.classList.remove('selected-player-card');
                        selectedPlayerCards = selectedPlayerCards.filter(selectedCard =>
                            !(selectedCard.id === id)
                        );
                    } else {
                        if (!data.maxPlayersCardsSelectable || selectedPlayerCards.length < data.maxPlayersCardsSelectable) {
                            card.classList.add('selected-player-card');
                            selectedPlayerCards.push({ id: id, rank: rank, suit: suit, card_type: cardType });
                        } else {
                            showNotification(`Max number of selected hand cards is ${data.maxPlayersCardsSelectable}. Deselect one before selecting another.`, 3000);
                        }
                    }
                };
            } else {
                card.style.cursor = 'not-allowed';
                card.onclick = null;
            }
        });
    });

    function displayPlayerCards(player, points) {
        const playground = document.getElementById('playground');

        const playerFrame = document.createElement('div');
        playerFrame.className = 'player-frame';
        playerFrame.style.position = 'absolute';

        const nameLabel = document.createElement('span');
        nameLabel.id = player.player_email
        nameLabel.textContent = `${player.player_email}: ${points}`;
        nameLabel.className = 'name-label';

        const cardsFrame = document.createElement('div');
        cardsFrame.className = 'cards-frame';

        player.cards.forEach(card => {
            const cardElement = document.createElement('img');
            cardElement.className = 'player-card-image';
            cardElement.src = `/static/imgs/${card.rank}_of_${card.suit}.png`;
            cardElement.style.cursor = 'not-allowed';
            cardElement.dataset.id = card.id;
            cardElement.dataset.rank = card.rank;
            cardElement.dataset.suit = card.suit;
            cardElement.dataset.cardType = card.card_type

            cardsFrame.appendChild(cardElement);
        });

        playerFrame.appendChild(cardsFrame);
        playerFrame.appendChild(nameLabel);
        playground.appendChild(playerFrame);
    }

    function removeTableCard(card) {
        const index = selected_table_cards.findIndex(c => c.rank === card.rank && c.suit === card.suit);

        if (index !== -1) {
            selected_table_cards.splice(index, 1);
        }
    }

    function showNotification(message, duration = 3000) {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, duration);
    }

    socket.on('game_over', (data) => {
        showNotification(data.message, 3000);

        setTimeout(() => {
            socket.emit('load_logged_users')
        }, 3000);
    });

    socket.on('game_rules', (data) => {
        showAlert(data.rules)
    });

});


function logout() {
    socket.emit('logout')

    socket.on('successful_logout', data => {
         window.location.href = '/'
    });
}

function finishMove() {
    socket.emit('finish_move', game_id, selected_table_cards, selectedPlayerCards)
}

function gameRules() {
    socket.emit('game_rules', selected_game.name)
}

function showModal(message, onAccept, onDecline) {
    const modal = document.getElementById('custom-modal');
    const modalMessage = document.getElementById('modal-message');
    const closeButton = document.querySelector('.close');
    const acceptButton = document.getElementById('modal-accept');
    const declineButton = document.getElementById('modal-decline');

    modalMessage.innerHTML = '';
    if (message instanceof HTMLElement) {
        modalMessage.appendChild(message)
    } else {
        modalMessage.innerHTML = message;
    }
    modal.style.display = 'flex';

    closeButton.onclick = () => {
        modal.style.display = 'none';
        if (onDecline) onDecline();
    };

    acceptButton.onclick = () => {
        modal.style.display = 'none';
        if (onAccept) onAccept();
    };

    declineButton.onclick = () => {
        modal.style.display = 'none';
        if (onDecline) onDecline();
    };

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
            if (onDecline) onDecline();
        }
    };
}

function showAlert(message, onOk) {
    const declineButton = document.getElementById('modal-decline');
    const acceptButton = document.getElementById('modal-accept');


    declineButton.style.display = 'none';
    acceptButton.textContent = 'OK';

    showModal(message, () => {
        onOk();
        const modal = document.getElementById('custom-modal');
        modal.style.display = 'none';
        declineButton.style.display = '';
        acceptButton.textContent = 'Accept';
    }, null);
}

function showLoader() {
    const loaderOverlay = document.getElementById('loader-overlay');
    loaderOverlay.style.visibility = 'visible';
}

function hideLoader() {
    const loaderOverlay = document.getElementById('loader-overlay');
    loaderOverlay.style.visibility = 'hidden';
}

