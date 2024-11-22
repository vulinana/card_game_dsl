from .player import Player
from dataclasses import dataclass, asdict

@dataclass
class Action:
    def __init__(self, model):
        self.action_type = model.action_type
        self.condition = model.condition

    def to_dict(self):
        return asdict(self)