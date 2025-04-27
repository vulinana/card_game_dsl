from dataclasses import dataclass, asdict, field

from .card_count import CardCount
from .rules import Rules
from typing import List

from .state import State


@dataclass
class CardGame:
    name: str
    cards: List[CardCount] = field(default_factory=list)
    states: List[State] = field(default_factory=list)

    def __init__(self, model):
        self.name = model.name
        self.rules = Rules(model.rules)
        self.cards = [CardCount(cc.card, cc.score, cc.count) for cc in getattr(model.cards, "cards", []) or []]
        self.states = [State(s) for s in model.states.states]

    def to_dict(self):
        return asdict(self)