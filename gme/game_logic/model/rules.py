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
        self.actions = [Action(a) for a in model.actions]

    def to_dict(self):
        return asdict(self)