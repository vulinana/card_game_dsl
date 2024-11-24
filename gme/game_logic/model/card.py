from dataclasses import dataclass, asdict


@dataclass
class Card:
    rank: str
    suit: str

    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def to_dict(self):
        return asdict(self)