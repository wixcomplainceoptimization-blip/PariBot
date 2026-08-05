from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    balance = db.Column(db.Float, default=100.0)
    total_won = db.Column(db.Float, default=0.0)
    total_lost = db.Column(db.Float, default=0.0)
    games_played = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'balance': round(self.balance, 2),
            'total_won': round(self.total_won, 2),
            'total_lost': round(self.total_lost, 2),
            'games_played': self.games_played
        }

class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), nullable=False)
    bet_amount = db.Column(db.Float, nullable=False)
    win_amount = db.Column(db.Float, default=0.0)
    result = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'bet': round(self.bet_amount, 2),
            'win': round(self.win_amount, 2),
            'result': self.result,
            'time': self.created_at.isoformat()
        }
