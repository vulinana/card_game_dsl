from extensions import db

# Korisnik
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    user_games = db.relationship('UserGame', back_populates='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.username}>'


# Igra
class GameDB(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

    user_games = db.relationship('UserGame', back_populates='game', cascade="all, delete-orphan")
    game_cards = db.relationship('GameCard', back_populates='game', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Game {self.name}>'


# Karta
class CardDB(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    rank = db.Column(db.String(80), nullable=False)
    suit = db.Column(db.String(80), nullable=False)

    game_cards = db.relationship('GameCard', back_populates='card', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Card {self.rank} {self.suit}>'


# Veza između igre i korisnika (M:N)
class UserGame(db.Model):
    __tablename__ = 'users_games'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), primary_key=True)

    user = db.relationship('User', back_populates='user_games')
    game = db.relationship('GameDB', back_populates='user_games')

    user_game_cards = db.relationship('UserGameCard', back_populates='user_game', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<UserGame user_id={self.user_id} game_id={self.game_id}>'


# Veza između igre i karata (M:N)
class GameCard(db.Model):
    __tablename__ = 'game_cards'
    id = db.Column(db.Integer, primary_key=True)  # Jedinstveni ID za svaki zapis
    game_id = db.Column(db.Integer, db.ForeignKey('games.id', ondelete='CASCADE'), nullable=False)
    card_id = db.Column(db.Integer, db.ForeignKey('cards.id', ondelete='CASCADE'), nullable=False)

    game = db.relationship('GameDB', back_populates='game_cards')
    card = db.relationship('CardDB', back_populates='game_cards')

    __table_args__ = (
        db.Index('ix_game_card', 'game_id', 'card_id'),  # Složeni indeks
    )

    def __repr__(self):
        return f'<GameCard game_id={self.game_id} card_id={self.card_id}>'


# Veza između korisnika, igre i karata
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