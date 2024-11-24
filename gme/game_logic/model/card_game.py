from dataclasses import dataclass, asdict, field

from .card_count import CardCount
from .rules import Rules
from .player import Player
from .round import Round
from typing import List

@dataclass
class CardGame:
    name: str
    players: List[Player] = field(default_factory=list)
    rounds: List[Round] = field(default_factory=list)
    cards: List[CardCount] = field(default_factory=list)

    def __init__(self, model):
        self.name = model.name
        self.rules = Rules(model.rules)
        self.players = [Player(p) for p in model.players]
        self.rounds = [Round(r) for r in model.rounds]
        self.cards = [CardCount(cc.card, cc.count) for cc in model.cards]

    def to_dict(self):
        return asdict(self)