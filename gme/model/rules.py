from dataclasses import dataclass, asdict

@dataclass
class Rules:
    def __init__(self, model):
        self.min_players = model.min_players
        self.max_players = model.max_players
        self.rounds = model.rounds
        self.table_cards_visible = (model.table_cards_visible is None) or (str(model.table_cards_visible).lower() == "true")
        self.next_player_in_round_condition = model.next_player_in_round_condition
        self.game_winner = model.game_winner

        if self.min_players <= 0:
            raise ValueError("min_players must be greater than 0")
        if self.max_players <= 0:
            raise ValueError("max_players must be greater than 0")
        if self.min_players > self.max_players:
            raise ValueError("min_players cannot be greater than max_players")

    def to_dict(self):
        return asdict(self)

    def to_text(self):
        conditions = {
            "highest_score": "The winner is the player with the highest score.<br>",
            "lowest_score": "The winner is the player with the lowest score.<br>",
            "winner": "The round next player is the winner of the round.<br>",
            "circle_order": "The next player follows the order of the circle (turns are taken sequentially).<br>",
        }

        return (
            f"Minimum players: {self.min_players}<br>"
            f"Maximum players: {self.max_players}<br>"
            f"Rounds: {self.rounds}<br>"
            f"{conditions.get(self.game_winner, '')}"
            f"{conditions.get(self.next_player_in_round_condition, '')}"
        )
