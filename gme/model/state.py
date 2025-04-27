from dataclasses import dataclass, asdict, field
from typing import List

from gme.model.transition import Transition
from gme.model.action import Action


@dataclass
class State:
    name: str
    action: Action
    transitions: List[Transition] = field(default_factory=list)
    def __init__(self, state):
        self.name = state.name
        self.action = Action(state.action)
        self.transitions = [Transition(t) for t in state.transitions]

    def to_dict(self):
        return asdict(self)