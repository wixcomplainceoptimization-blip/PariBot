from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, User, GameHistory
import hashlib
import hmac
import json
import random
import os

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = Config.SECRET_KEY

CORS(app)
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

def verify_telegram_data(init_data):
    """Verify Telegram WebApp initData"""
    try:
        data = dict(x.split('=') for x in init_data.split('&') if x)
        hash_value = data.pop('hash', None)
        
        if not hash_value:
            return False
        
        # Sort and create check string
        check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
        
        # Generate secret key
        secret_key = hmac.new(
            b"WebAppData",
            Config.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == hash_value
    except Exception as e:
        print(f"Verification error: {e}")
        return False

def get_user_from_init_data(init_data):
    """Extract user data from initData"""
    try:
        data = dict(x.split('=') for x in init_data.split('&') if x)
        user_data = json.loads(data.get('user', '{}'))
        return {
            'id': str(user_data.get('id')),
            'username': user_data.get('username', 'Anonymous'),
            'first_name': user_data.get('first_name', 'User')
        }
    except:
        return None

@app.route('/')
def serve_index():
    """Serve the WebApp frontend"""
    return send_from_directory('static', 'index.html')

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/api/user', methods=['POST'])
def get_or_create_user():
    try:
        data = request.json
        init_data = data.get('initData')
        
        if not verify_telegram_data(init_data):
            return jsonify({'error': 'Invalid authentication'}), 401
        
        user_info = get_user_from_init_data(init_data)
        if not user_info:
            return jsonify({'error': 'Invalid user data'}), 400
        
        telegram_id = user_info['id']
        username = user_info['username']
        first_name = user_info['first_name']
        
        # Get or create user
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                balance=Config.INITIAL_BALANCE
            )
            db.session.add(user)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        print(f"Error in get_user: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spin', methods=['POST'])
def spin():
    try:
        data = request.json
        init_data = data.get('initData')
        bet_amount = float(data.get('bet', 1))
        
        if not verify_telegram_data(init_data):
            return jsonify({'error': 'Invalid authentication'}), 401
        
        if bet_amount < Config.MIN_BET or bet_amount > Config.MAX_BET:
            return jsonify({'error': f'Bet must be between {Config.MIN_BET} and {Config.MAX_BET}'}), 400
        
        user_info = get_user_from_init_data(init_data)
        telegram_id = user_info['id']
        
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if bet_amount > user.balance:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # Spin logic - 50/50 chance
        win = random.random() > 0.5
        win_amount = bet_amount * 2 if win else 0
        
        # Update balance
        if win:
            user.balance += bet_amount  # Net profit = bet amount (since we bet, win = bet*2)
            user.total_won += bet_amount
        else:
            user.balance -= bet_amount
            user.total_lost += bet_amount
        
        user.games_played += 1
        
        # Save history
        history = GameHistory(
            telegram_id=telegram_id,
            bet_amount=bet_amount,
            win_amount=win_amount,
            result='win' if win else 'lose',
            game_type='spin'
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'win': win,
            'bet': bet_amount,
            'win_amount': round(win_amount, 2),
            'new_balance': round(user.balance, 2),
            'total_won': round(user.total_won, 2),
            'total_lost': round(user.total_lost, 2),
            'games_played': user.games_played
        })
        
    except Exception as e:
        print(f"Error in spin: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['POST'])
def get_history():
    try:
        data = request.json
        init_data = data.get('initData')
        
        if not verify_telegram_data(init_data):
            return jsonify({'error': 'Invalid authentication'}), 401
        
        user_info = get_user_from_init_data(init_data)
        telegram_id = user_info['id']
        
        history = GameHistory.query.filter_by(telegram_id=telegram_id).order_by(
            GameHistory.created_at.desc()
        ).limit(20).all()
        
        return jsonify({
            'success': True,
            'history': [h.to_dict() for h in history]
        })
        
    except Exception as e:
        print(f"Error in history: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=False)
