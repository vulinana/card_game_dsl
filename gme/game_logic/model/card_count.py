from dataclasses import dataclass, asdict

from gme.game_logic.model.card import Card


@dataclass
class CardCount:
    card: Card
    count: int

    def __init__(self, card, count):
        self.card = Card(card.rank, card.suit)
        self.count = count

    def to_dict(self):
        return asdict(self)

