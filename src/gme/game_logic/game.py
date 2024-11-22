from .model.card import Card

def check_card_points(card):
    if card.rank == '10' and card.suit == 'diamonds':
        return 2
    if card.rank == '10' or card.rank == 'A' or card.rank == '12' or card.rank == '13' or card.rank == '14' or (
            card.rank == '2' and card.suit == 'clubs'):
        return 1


class Game:
    instance = None
    gui = None
    round = 0
    player_points = [0]

    def __new__(cls, gui=None):
        if cls.instance is None:
            cls.instance = super(Game, cls).__new__(cls)
            cls.instance.gui = gui
        return cls.instance

    def validate_points(self):
        total_table_value = sum(int(card.rank) for card in self.gui.selected_table_cards)
        if int(self.gui.selected_player_card.rank) == total_table_value:
            self.player_points[0] += check_card_points(self.gui.selected_player_card)
            for card in self.gui.selected_table_cards:
                self.player_points[0] += check_card_points(card)
                print(self.player_points[0])
            self.gui.update_player_score_and_remove_cards()

    def next_round(self):
        if all(len(hand.hand_cards) == 0 for hand in self.gui.current_game.rounds[self.round].player_hands):
            self.round += 1
            if self.round >= self.gui.current_game.rules.number_of_rounds:
                if self.player_points[0] > 0:
                    self.gui.finish_game("You won!", "green")
                else:
                    self.gui.finish_game("You lost!", "red")
            else:
                self.gui.draw_next_round()

    def reset(self):
        self.round = 0
        self.player_points[0] = 0

