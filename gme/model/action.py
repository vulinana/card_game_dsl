from dataclasses import dataclass, asdict, field
from typing import List



@dataclass
class Action:
    name: str
    params: List[any] = field(default_factory=list)
    def __init__(self, state):
        self.name = state.name
        raw_params = getattr(state.params, "params", []) or []
        self.params = [getattr(p, "value", None) for p in raw_params]

    def to_dict(self):
        return asdict(self)