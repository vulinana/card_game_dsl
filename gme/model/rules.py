from dataclasses import dataclass, asdict

@dataclass
class Rules:
    def __init__(self, model):
        self.min_players = model.min_players
        self.max_players = model.max_players
        self.rounds = model.rounds
        self.table_cards_visible = (model.table_cards_visible or "").lower() in ("true", "yes")
        self.next_player_in_round_condition = model.next_player_in_round_condition
        self.game_winner = model.game_winner

    def to_dict(self):
        return asdict(self)

    def to_text(self):
        text = (
            f"Minimum number of players: {self.min_players}<br>"
            f"Maximum number of players: {self.max_players}<br>"
            f"Number of rounds: {self.rounds}<br>"
        )

        if self.game_winner == "highest_score":
            text += (
                f"The winner is the player with the highest score.<br>"
            )
        elif self.game_winner == "lowest_score":
            text += (
                f"The winner is the player with the lowest score.<br>"
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
