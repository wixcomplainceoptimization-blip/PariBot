from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    favorite_sport = Column(String(50))
    favorite_league = Column(String(100))
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    match_id = Column(String(200))
    league = Column(String(100))
    home_team = Column(String(100))
    away_team = Column(String(100))
    prediction = Column(String(50))
    confidence = Column(Float)
    home_odds = Column(Float)
    draw_odds = Column(Float)
    away_odds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    match_time = Column(DateTime)
    
class BetHistory(Base):
    __tablename__ = 'bet_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    match = Column(String(200))
    bet_type = Column(String(50))
    odds = Column(Float)
    stake = Column(Float)
    result = Column(String(50))
    profit = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    match = Column(String(200))
    target_odds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered = Column(Boolean, default=False)

# Create tables
Base.metadata.create_all(engine)

class Database:
    """Database operations for PariBot"""
    
    @staticmethod
    def get_session():
        return SessionLocal()
    
    @staticmethod
    def add_user(telegram_id, username=None, first_name=None, last_name=None):
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.commit()
                return user
            else:
                # Update last active
                user.last_active = datetime.utcnow()
                session.commit()
                return user
        finally:
            session.close()
    
    @staticmethod
    def update_user_preferences(telegram_id, sport=None, league=None):
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                if sport:
                    user.favorite_sport = sport
                if league:
                    user.favorite_league = league
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    @staticmethod
    def save_prediction(prediction_data):
        session = SessionLocal()
        try:
            pred = Prediction(
                match_id=prediction_data.get('match_id', ''),
                league=prediction_data.get('league', ''),
                home_team=prediction_data.get('home_team', ''),
                away_team=prediction_data.get('away_team', ''),
                prediction=prediction_data.get('prediction', ''),
                confidence=prediction_data.get('confidence', 0),
                home_odds=prediction_data.get('home_odds', 0),
                draw_odds=prediction_data.get('draw_odds', 0),
                away_odds=prediction_data.get('away_odds', 0),
                match_time=prediction_data.get('match_time')
            )
            session.add(pred)
            session.commit()
        finally:
            session.close()
    
    @staticmethod
    def get_recent_predictions(limit=10):
        session = SessionLocal()
        try:
            predictions = session.query(Prediction).order_by(
                Prediction.created_at.desc()
            ).limit(limit).all()
            return predictions
        finally:
            session.close()
    
    @staticmethod
    def save_bet(user_id, match, bet_type, odds, stake):
        session = SessionLocal()
        try:
            bet = BetHistory(
                user_id=user_id,
                match=match,
                bet_type=bet_type,
                odds=odds,
                stake=stake
            )
            session.add(bet)
            session.commit()
        finally:
            session.close()
    
    @staticmethod
    def add_alert(user_id, match, target_odds):
        session = SessionLocal()
        try:
            alert = Alert(
                user_id=user_id,
                match=match,
                target_odds=target_odds
            )
            session.add(alert)
            session.commit()
        finally:
            session.close()
