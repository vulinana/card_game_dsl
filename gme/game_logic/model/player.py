from dataclasses import dataclass, asdict

@dataclass
class Player:
    number: int

    def __init__(self, model):
        self.number = model.number

    def to_dict(self):
        return asdict(self)