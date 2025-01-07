from dataclasses import dataclass, asdict

@dataclass
class Action:
    def __init__(self, model):
        self.action_type = model.action_type
        self.condition = model.condition

    def to_dict(self):
        return asdict(self)

    def to_text(self):
        text = ""
        if self.action_type == "collect_by_rank":
            text = ("The player must collect points by gathering cards with the same rank as their own card,"
                    " or by forming combinations of cards that match the rank of their card.<br>")
        if self.action_type == "follow_by_rank":
            text = "The player can win the round if they play a card of the same rank as the round initiator's card.<br>"
        if self.action_type == "follow_by_suit":
            text = "The player can win the round if they play a card of the same suit as the round initiator's card.<br>"
        if self.action_type == "follow_by_rank_or_suit":
            text = "The player can win the round if they play a card of the same rank or suit as the round initiator's card.<br>"
        return text