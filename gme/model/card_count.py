from dataclasses import dataclass, asdict

from gme.model.card import Card


@dataclass
class CardCount:
    card: Card
    score: int
    count: int


    def __init__(self, card, score, count):
        self.card = Card(card.rank, card.suit)
        self.score = score
        self.count = count

    def to_dict(self):
        return asdict(self)

