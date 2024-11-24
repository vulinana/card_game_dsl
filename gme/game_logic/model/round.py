from dataclasses import dataclass, asdict, field
from typing import List

from .card import Card
from .player_hand import PlayerHand

@dataclass
class Round:
    name: str
    player_hands: List[PlayerHand] = field(default_factory=list)
    table_cards: List[Card] = field(default_factory=list)

    def __init__(self, model):
        self.name = model.name
        self.player_hands = [PlayerHand(p) for p in model.player_hands]
        self.table_cards = [Card(c.rank, c.suit) for c in model.table_cards]

    def to_dict(self):
        return asdict(self)