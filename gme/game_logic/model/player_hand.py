from typing import List

from .player import Player
from .card import Card

from dataclasses import dataclass, asdict, field


@dataclass
class PlayerHand:
    player: Player
    hand_cards: List[Card] = field(default_factory=list)

    def __init__(self, model):
        self.player = Player(model.player)
        self.hand_cards = [Card(c.rank, c.suit) for c in model.hand_cards]

    def to_dict(self):
        return asdict(self)
