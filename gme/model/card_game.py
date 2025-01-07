from dataclasses import dataclass, asdict, field

from .action import Action
from .card_count import CardCount
from .rules import Rules
from typing import List

@dataclass
class CardGame:
    name: str
    cards: List[CardCount] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)

    def __init__(self, model):
        self.name = model.name
        self.rules = Rules(model.rules)
        self.cards = [CardCount(cc.card, cc.score, cc.count) for cc in model.cards]
        self.actions = [Action(a) for a in model.actions]

    def to_dict(self):
        return asdict(self)