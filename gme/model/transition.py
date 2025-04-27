from dataclasses import dataclass, asdict, field
from typing import List


@dataclass
class Transition:
    nextState: str
    condition: bool
    def __init__(self, transition):
        self.nextState = transition.nextState.name
        self.condition = transition.condition

    def to_dict(self):
        return asdict(self)