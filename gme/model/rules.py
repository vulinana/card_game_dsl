from dataclasses import dataclass, asdict

from .action import Action

@dataclass
class Rules:
    def __init__(self, model):
        self.min_number_of_players = model.min_number_of_players
        self.max_number_of_players = model.max_number_of_players
        self.number_of_rounds = model.number_of_rounds
        self.number_of_cards_per_round = model.number_of_cards_per_round
        self.number_of_table_cards = model.number_of_table_cards
        self.winner_condition = model.winner_condition
        self.new_round_condition = model.new_round_condition
        self.next_player_in_round_condition = model.next_player_in_round_condition

    def to_dict(self):
        return asdict(self)

    def to_text(self):
        text = (
            f"Minimum number of players: {self.min_number_of_players}<br>"
            f"Maximum number of players: {self.max_number_of_players}<br>"
            f"Number of rounds: {self.number_of_rounds}<br>"
            f"Cards per round: {self.number_of_cards_per_round}<br>"
            f"Number of table cards: {self.number_of_table_cards}<br>"
        )

        if self.winner_condition == "highest_score":
            text += (
                f"The winner is the player with the highest score.<br>"
            )
        elif self.winner_condition == "lowest_score":
            text += (
                f"The winner is the player with the lowest score.<br>"
            )

        if self.new_round_condition == "no_cards_left":
            text += (
                f"The round ends when no cards are left to play.<br>"
            )
        elif self.new_round_condition == "circle_completed":
            text += (
                f"The round ends when the circle is completed.<br>"
            )

        if self.next_player_in_round_condition == "winner":
            text += (
                f"The round next player is the winner of the round.<br>"
            )
        elif self.next_player_in_round_condition == "circle_order":
            text += (
                f"The next player follows the order of the circle (turns are taken sequentially).<br>"
            )

        return text
