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

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = Config.SECRET_KEY

CORS(app)
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

def verify_telegram_data(init_data):
    """Verify Telegram WebApp data"""
    try:
        data = dict(x.split('=') for x in init_data.split('&') if x)
        hash_value = data.pop('hash', None)
        
        if not hash_value:
            return False
        
        check_string = '\n'.join(f"{k}={v}" for k, v in sorted(data.items()))
        
        secret_key = hmac.new(
            b"WebAppData",
            Config.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return calculated_hash == hash_value
    except:
        return False

def get_user_data(init_data):
    """Extract user info from initData"""
    try:
        data = dict(x.split('=') for x in init_data.split('&') if x)
        user_json = data.get('user', '{}')
        user_data = json.loads(user_json)
        return {
            'id': str(user_data.get('id')),
            'username': user_data.get('username', 'Anonymous'),
            'first_name': user_data.get('first_name', 'User')
        }
    except:
        return None

# ==================== ROUTES ====================

@app.route('/')
def serve_index():
    """Serve the mini app"""
    return send_from_directory('static', 'index.html')

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/api/user', methods=['POST'])
def get_user():
    try:
        data = request.json
        init_data = data.get('initData')
        
        if not verify_telegram_data(init_data):
            return jsonify({'error': 'Invalid auth'}), 401
        
        user_info = get_user_data(init_data)
        if not user_info:
            return jsonify({'error': 'Invalid user data'}), 400
        
        user = User.query.filter_by(telegram_id=user_info['id']).first()
        if not user:
            user = User(
                telegram_id=user_info['id'],
                username=user_info['username'],
                first_name=user_info['first_name'],
                balance=Config.INITIAL_BALANCE
            )
            db.session.add(user)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/spin', methods=['POST'])
def spin():
    try:
        data = request.json
        init_data = data.get('initData')
        bet = float(data.get('bet', 1))
        
        if not verify_telegram_data(init_data):
            return jsonify({'error': 'Invalid auth'}), 401
        
        if bet < Config.MIN_BET or bet > Config.MAX_BET:
            return jsonify({'error': f'Bet must be between {Config.MIN_BET} and {Config.MAX_BET}'}), 400
        
        user_info = get_user_data(init_data)
        user = User.query.filter_by(telegram_id=user_info['id']).first()
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if bet > user.balance:
            return jsonify({'error': 'Insufficient balance'}), 400
        
        # 50/50 chance
        win = random.random() > 0.5
        win_amount = bet * 2 if win else 0
        
        if win:
            user.balance += bet
            user.total_won += bet
        else:
            user.balance -= bet
            user.total_lost += bet
        
        user.games_played += 1
        
        history = GameHistory(
            telegram_id=user.telegram_id,
            bet_amount=bet,
            win_amount=win_amount,
            result='win' if win else 'lose'
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'win': win,
            'win_amount': round(win_amount, 2),
            'new_balance': round(user.balance, 2),
            'total_won': round(user.total_won, 2),
            'total_lost': round(user.total_lost, 2),
            'games_played': user.games_played
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['POST'])
def get_history():
    try:
        data = request.json
        init_data = data.get('initData')
        
        if not verify_telegram_data(init_data):
            return jsonify({'error': 'Invalid auth'}), 401
        
        user_info = get_user_data(init_data)
        history = GameHistory.query.filter_by(
            telegram_id=user_info['id']
        ).order_by(GameHistory.created_at.desc()).limit(20).all()
        
        return jsonify({
            'success': True,
            'history': [h.to_dict() for h in history]
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
