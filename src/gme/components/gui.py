import tkinter as tk
import copy
from functools import partial

from src.gme.components.interface import Interface
from src.gme.game_logic.model.card_game import CardGame
from PIL import Image, ImageTk
from src.gme.game_logic.game import Game
from src.gme.game_logic.model.card import Card


class TkinterGui(Interface):
    window = tk.Tk()
    card_games: list[CardGame] = []
    current_game: CardGame
    selected_player = None
    selected_table_cards = []
    selected_player_card = Card('-1', '-1')
    score_labels = []
    center_frame = None
    playground = None

    def __init__(self, card_games):
        super().__init__()
        self.game = Game(self)
        self.card_games = card_games
        self.current_game = copy.deepcopy(self.card_games[0])
        self.selected_game_button = None

        self.window.title("Card games")
        self.window.state('zoomed')

        self.sidebar = tk.Frame(self.window, bg="brown")
        self.toolbar = tk.Frame(self.window, bg="beige")

        self.sidebar.place(x=0, y=0, relwidth=0.15, relheight=1)
        self.toolbar.place(relx=0.15, rely=0.95, relwidth=0.85, relheight=0.05)
        self.sidebar.columnconfigure(0, weight=1)

        self.draw_card_games()

        # Oznacavanje prvog dugmeta kao selektovanog
        if self.card_games:
            self.select_game(self.card_games[0], self.sidebar.winfo_children()[0])


    def finish_move(self):
        if len(self.selected_table_cards) == 0:
            self.current_game.rounds[self.game.round].table_cards.append(self.selected_player_card)
            self.remove_selected_cards()

            self.draw_table_cards(self.current_game.rounds[self.game.round].table_cards)
            self.selected_player_card = Card('-1', '-1')
        else:
            self.game.validate_points()

        self.game.next_round()

    def initiate(self):
        self.game.reset()

        for widget in self.toolbar.winfo_children():
            widget.destroy()

        self.playground = tk.Frame(self.window, bg="white")
        self.playground.place(relx=0.15, y=0, relwidth=0.85, relheight=0.95)

        self.center_frame = tk.Frame(self.playground, bg="white")
        self.center_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.create_player_selection(self.current_game.players)
        self.window.mainloop()

    def draw_card_games(self):
        for idx, card_game in enumerate(self.card_games):
            btn = tk.Button(self.sidebar, height=2,
                            bg="beige", fg="brown", font=10, text=card_game.name, cursor="hand2")
            btn.grid(row=idx, column=0, sticky='nsew')
            btn.config(command=lambda cg=card_game, button=btn: self.select_game(cg, button))

    def select_game(self, card_game, btn):
        if self.selected_game_button:
            self.selected_game_button.config(bg="beige", fg="brown")

        btn.config(bg="#C4A484", fg="black")
        self.selected_game_button = btn

        self.current_game = copy.deepcopy(card_game)
        self.initiate()

    def create_player_selection(self, players):
        for idx, player in enumerate(players):
            player_button = tk.Button(self.center_frame, text=f"Player {player.number}",
                                      bg="beige", fg="brown", font=("Arial", 12), width=15,
                                      command=lambda p=player: self.select_player(p),
                                      cursor="hand2")
            player_button.grid(row=idx, column=0, padx=10, pady=5)

    def select_player(self, player):
        self.selected_player = player

        self.draw_on_toolbar()
        self.draw_table_cards(self.current_game.rounds[self.game.round].table_cards)
        self.draw_players_cards()

    def draw_on_toolbar(self):
        finish_move_button = tk.Button(
            self.toolbar, text="Finish Move", bg="green", fg="white", font=("Arial", 12),
            command=lambda: self.finish_move(), cursor="hand2"
        )
        finish_move_button.place(relx=0.5, rely=0.5, anchor='center')
        self.round_label = tk.Label(self.toolbar, text=f'Round: {self.game.round}', bg='beige', fg="brown",
                                    font=("Arial", 12))
        self.round_label.place(relx=0.01, rely=0.5, anchor='w')

    def draw_table_cards(self, cards):
        for widget in self.center_frame.winfo_children():
            widget.destroy()

        for idx, card in enumerate(cards):
            image = Image.open(f"src/gme/imgs/{card.rank}_of_{card.suit}.png")
            image = image.resize((70, 110))
            card_image = ImageTk.PhotoImage(image)

            card_label = tk.Label(self.center_frame, image=card_image, bg="white")
            card_label.image = card_image
            card_label.card = card
            card_label.pack(side=tk.LEFT, padx=10, pady=10)

            card_label.bind("<Button-1>", lambda e, c=card, l=card_label: self.select_table_card(c, l))
            card_label.bind("<Enter>", lambda e, label=card_label: self.change_cursor(label, "hand2", e))
            card_label.bind("<Leave>", lambda e, label=card_label: self.change_cursor(label, "", e))

    def draw_players_cards(self):
        for hand in self.current_game.rounds[self.game.round].player_hands:
            if hand.player.number == self.selected_player.number:
                label = self.draw_cards(hand, position='bottom')
                self.score_labels.append(label)
            else:
                label = self.draw_cards(hand, position='top')
                self.score_labels.append(label)

    def draw_cards(self, hand, position='top'):
        cards = hand.hand_cards
        player = hand.player.number

        cards_frame = tk.Frame(self.playground, bg="white")

        if position == 'top':
            cards_frame.place(relx=0.5, rely=0.02, anchor='n')

            name_frame = tk.Frame(cards_frame, bg="white")
            name_frame.pack(side=tk.TOP, pady=(0, 3))

            name_label = tk.Label(name_frame, text=f"Player {player} :", bg="white", fg="brown", font=("Arial", 12))
            name_label.pack(side=tk.LEFT, pady=(0, 3))

            score_label = tk.Label(name_frame, text=str(self.game.player_points[0]), bg="white", fg="brown",
                                   font=("Arial", 12))
            score_label.pack(side=tk.LEFT, pady=(0, 3), padx=(5, 0))

        elif position == 'bottom':
            cards_frame.place(relx=0.5, rely=0.98, anchor='s')

            name_frame = tk.Frame(cards_frame, bg="white")
            name_frame.pack(side=tk.BOTTOM, pady=(0, 3))

            name_label = tk.Label(name_frame, text=f"Player {player} :", bg="white", fg="brown", font=("Arial", 12))
            name_label.pack(side=tk.LEFT, pady=(0, 3))

            score_label = tk.Label(name_frame, text=str(self.game.player_points[0]), bg="white", fg="brown",
                                   font=("Arial", 12))
            score_label.pack(side=tk.LEFT, pady=(0, 3), padx=(5, 0))
        else:
            cards_frame.pack(side=tk.TOP, pady=10)

        for idx, card in enumerate(cards):
            if position == 'bottom':
                image = Image.open(f"src/gme/imgs/{card.rank}_of_{card.suit}.png")
            else:
                image = Image.open("src/gme/imgs/card_background.png")
            image = image.resize((70, 110))
            card_image = ImageTk.PhotoImage(image)

            card_label = tk.Label(cards_frame, image=card_image, bg="white")
            card_label.image = card_image
            card_label.card = card
            card_label.pack(side=tk.LEFT, padx=5, pady=5)

            if position == 'bottom':
                card_label.bind("<Button-1>", lambda e, c=card, p=player, l=card_label: self.select_player_card(c, l))
                card_label.bind("<Enter>", lambda e, label=card_label: self.change_cursor(label, "hand2", e))
                card_label.bind("<Leave>", lambda e, label=card_label: self.change_cursor(label, "", e))

        return score_label

    def change_cursor(self, label, cursor, event=None):
        label.config(cursor=cursor)

    def select_table_card(self, card, label):
        if card in self.selected_table_cards:
            self.selected_table_cards.remove(card)
            label.config(bd=0)
        else:
            self.selected_table_cards.append(card)
            label.config(bd=2, relief="solid", highlightbackground="red")

    def select_player_card(self, card, label):
        if self.selected_player_card == card:
            self.selected_player_card = Card('-1', '-1')
            label.config(bd=0)
        else:
            if self.selected_player_card.rank != '-1':
                self.selected_player_card_label.config(bd=0)
            self.selected_player_card = card
            self.selected_player_card_label = label
            label.config(bd=2, relief="solid", highlightbackground="blue")

    def update_player_score_and_remove_cards(self):
        self.score_labels[1].config(text=f"{self.game.player_points[0]}")
        self.remove_selected_cards()

    def remove_selected_cards(self):
        for hand in self.current_game.rounds[self.game.round].player_hands:
            if hand.player.number == self.selected_player.number:
                hand.hand_cards.remove(self.selected_player_card)

        card_label = self.find_card_label(self.selected_player_card)
        if card_label:
            card_label.destroy()
        self.selected_player_card = Card('-1', '-1')

        for card in self.selected_table_cards:
            self.current_game.rounds[self.game.round].table_cards.remove(card)
            card_label = self.find_card_label(card)
            if card_label:
                card_label.destroy()
        self.selected_table_cards.clear()

    def find_card_label(self, card):
        for widget in self.playground.winfo_children():
            if isinstance(widget, tk.Frame):
                for label in widget.winfo_children():
                    if isinstance(label, tk.Label) and getattr(label, 'card', None) == card:
                        return label
        return None

    def draw_next_round(self):
        message_label = tk.Label(self.playground, text="Next Round!", bg="red", fg="black", font=("Arial", 24))
        message_label.place(relx=0.5, rely=0.5, anchor='center')

        self.playground.after(2000, lambda: self.remove_message(message_label))
        self.playground.after(2000, self.draw_players_cards)
        self.playground.after(2000, lambda: self.round_label.config(text=f"Round: {self.game.round}"))

    @staticmethod
    def remove_message(message_label):
        message_label.destroy()

    def finish_game(self, message, color):
        message_label = tk.Label(self.playground, text=message, bg=color, fg="black", font=("Arial", 24))
        message_label.place(relx=0.5, rely=0.5, anchor='center')

        self.playground.after(2000, lambda: self.remove_message(message_label))
        self.playground.after(2000, lambda: self.playground.destroy())
        self.window.after(2000, lambda: self.initiate())




