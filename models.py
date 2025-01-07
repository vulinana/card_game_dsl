from sqlalchemy import Enum
import enum
from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    game_requests = db.relationship('GameRequest', back_populates='user')
    user_games = db.relationship('UserGame', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'


class GameDB(db.Model):
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    min_number_of_players = db.Column(db.Integer, nullable=True)
    max_number_of_players = db.Column(db.Integer, nullable=True)
    game_initiator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    current_player_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    number_of_rounds = db.Column(db.Integer)
    number_of_cards_per_round = db.Column(db.Integer)
    winner_condition = db.Column(db.String(80), nullable=True)
    new_round_condition = db.Column(db.String(80), nullable=True)
    next_player_in_round_condition = db.Column(db.String(80), nullable=True)

    game_initiator = db.relationship('User', foreign_keys=[game_initiator_id], backref='initiated_games')
    current_player = db.relationship('User', foreign_keys=[current_player_id], backref='current_games')

    game_requests = db.relationship('GameRequest', back_populates='game', cascade="all, delete-orphan")
    user_games = db.relationship('UserGame', back_populates='game', cascade="all, delete-orphan")
    table_cards = db.relationship('TableCard', back_populates='game', cascade="all, delete-orphan")
    game_cards = db.relationship('CardDB', back_populates='game', cascade="all, delete-orphan")
    pending_cards = db.relationship('PendingCard', back_populates='game', cascade="all, delete-orphan")
    game_actions = db.relationship('GameAction', back_populates='game', cascade="all, delete-orphan")
    rounds = db.relationship('Round', back_populates='game', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Game {self.name}>'

class GameAction(db.Model):
    __tablename__ = 'game_actions'

    id = db.Column(db.Integer, primary_key=True)
    action_type = db.Column(db.String(80), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)

    game = db.relationship('GameDB', back_populates='game_actions')
    def __repr__(self):
        return f'<GameAction {self.action_type}>'

class GameRequestStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"

class GameRequest(db.Model):
    __tablename__ = 'game_requests'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(Enum(GameRequestStatus), default=GameRequestStatus.PENDING, nullable=False)

    game = db.relationship('GameDB', back_populates='game_requests')
    user = db.relationship('User', back_populates='game_requests')

    def __repr__(self):
        return f'<GameRequest game_id={self.game_id} user_id={self.user_id} status={self.status}>'


class CardDB(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.String(80), nullable=False)
    suit = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=True)  # Foreign key

    game = db.relationship('GameDB', back_populates='game_cards')  #kojoj igri pripada karta ovo je sad bitno zbog score-a
    table_cards = db.relationship('TableCard', back_populates='card', cascade="all, delete-orphan") #table_cards

    def to_dict(self):
        return {
            'id': self.id,
            'rank': self.rank,
            'suit': self.suit
    }


class UserGame(db.Model):
    __tablename__ = 'users_games'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), primary_key=True)
    points = db.Column(db.Integer)

    user = db.relationship('User', back_populates='user_games')
    game = db.relationship('GameDB', back_populates='user_games')

    user_game_cards = db.relationship('UserGameCard', back_populates='user_game', cascade="all, delete-orphan")
    played_cards = db.relationship('PlayedCard', back_populates='user_game', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<UserGame user_id={self.user_id} game_id={self.game_id}>'


class TableCard(db.Model):
    __tablename__ = 'table_cards'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)

    game = db.relationship('GameDB', back_populates='table_cards')
    card = db.relationship('CardDB', back_populates='table_cards')

    __table_args__ = (
        db.Index('ix_game_card', 'game_id', 'card_id'),
    )

    def __repr__(self):
        return f'<TableCard game_id={self.game_id} card_id={self.card_id}>'


class UserGameCard(db.Model):
    __tablename__ = 'user_game_cards'
    id = db.Column(db.Integer, primary_key=True)  # Jedinstveni ID za svaki zapis
    user_id = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.Integer, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)

    user_game = db.relationship('UserGame', back_populates='user_game_cards')
    card = db.relationship('CardDB', backref='user_game_cards')

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['user_id', 'game_id'],
            ['users_games.user_id', 'users_games.game_id'],
            ondelete='CASCADE'
        ),
        db.Index('ix_user_game_card', 'user_id', 'game_id', 'card_id')  # Složeni indeks
    )

    def __repr__(self):
        return f'<UserGameCard user_id={self.user_id} game_id={self.game_id} card_id={self.card_id}>'

class PendingCard(db.Model):
    __tablename__ = 'pending_cards'
    id = db.Column(db.Integer, primary_key=True)  # Jedinstveni ID za svaki zapis
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    count = db.Column(db.Integer, nullable=False)

    game = db.relationship('GameDB', back_populates='pending_cards')
    card = db.relationship('CardDB')

    def __repr__(self):
        return f'<PendingCard game_id={self.game_id} card_id={self.card_id}>'

class CardTypeEnum(enum.Enum):
    PLAYER_CARD = 'player_card'
    TABLE_CARD = 'table_card'

class PlayedCard(db.Model):
    __tablename__ = 'played_cards'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.Integer, nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.id'))
    card_type = db.Column(Enum(CardTypeEnum), default=CardTypeEnum.PLAYER_CARD, nullable=False)

    user_game = db.relationship(
        'UserGame',
        back_populates='played_cards',
        primaryjoin='and_(PlayedCard.user_id == UserGame.user_id, PlayedCard.game_id == UserGame.game_id)'
    )
    card = db.relationship('CardDB', backref='played_cards')
    round = db.relationship('Round', back_populates='played_cards')

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['user_id', 'game_id'],
            ['users_games.user_id', 'users_games.game_id'],
            ondelete='CASCADE'
        ),
        db.Index('ix_user_game_played_card', 'user_id', 'game_id', 'card_id')
    )

    def __repr__(self):
        return f'<PlayedCard user_id={self.user_id} game_id={self.game_id} card_id={self.card_id}>'

class Round(db.Model):
    __tablename__ = 'rounds'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    round_initiator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)

    game = db.relationship('GameDB', back_populates='rounds')
    round_initiator = db.relationship('User', foreign_keys=[round_initiator_id], backref='initiated_rounds')
    winner = db.relationship('User', foreign_keys=[winner_id], backref='won_rounds')

    played_cards = db.relationship('PlayedCard', back_populates='round', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Round number={self.number} game_id={self.game_id} winner_id={self.winner_id}>'
