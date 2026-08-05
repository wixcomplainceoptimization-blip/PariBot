#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import json
import random
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import Config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Store user data in memory (will reset on restart)
users = {}

# ==================== HELPERS ====================

def get_user(user_id):
    """Get or create user data"""
    if user_id not in users:
        users[user_id] = {
            'balance': Config.INITIAL_BALANCE,
            'total_won': 0,
            'total_lost': 0,
            'games_played': 0
        }
    return users[user_id]

def format_balance(user_id):
    """Format user balance"""
    user = get_user(user_id)
    return f"💰 Balance: ${user['balance']:.2f}\n" \
           f"🎯 Games: {user['games_played']}\n" \
           f"✅ Won: ${user['total_won']:.2f}\n" \
           f"❌ Lost: ${user['total_lost']:.2f}"

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message"""
    user = update.effective_user
    user_id = str(user.id)
    
    # Initialize user
    get_user(user_id)
    
    welcome_message = f"""
🎲 *Welcome to PariBot!* 🎲

Hi {user.first_name}! I'm your betting assistant.

📋 *Available Commands:*
/start - Show this message
/balance - Check your balance
/bet <amount> - Place a bet (50/50 win chance)
/predict <league> - Get match predictions
/leagues - Show supported leagues
/help - Show help

💰 *Starting balance:* {Config.INITIAL_BALANCE} coins
🎯 *Min bet:* {Config.MIN_BET} coin
🎯 *Max bet:* {Config.MAX_BET} coins

⚠️ *Disclaimer:* For entertainment only!
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    help_text = """
🎲 *PariBot Help* 🎲

*Commands:*
/start - Show welcome message
/balance - Check your balance
/bet <amount> - Place a bet (50/50 win chance)
/predict <league> - Get match predictions
/leagues - Show supported leagues
/help - Show this help

*How to bet:*
Simply type: `/bet 10` to bet 10 coins

*Example:*
`/bet 25` - Bet 25 coins

*Leagues:*
/predict epl - Premier League predictions
/predict laliga - La Liga predictions
/predict seriea - Serie A predictions

*RULES:*
- 50/50 chance to win
- Win = get 2x your bet
- Start with {Config.INITIAL_BALANCE} coins
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check user balance"""
    user_id = str(update.effective_user.id)
    get_user(user_id)  # Ensure user exists
    await update.message.reply_text(format_balance(user_id), parse_mode='Markdown')

async def leagues_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show supported leagues"""
    league_text = "⚽ *Supported Leagues*\n\n"
    for key, name in Config.LEAGUES.items():
        league_text += f"• {name}\n"
        league_text += f"  (use: `/predict {key}`)\n\n"
    
    league_text += "\n💡 *Example:* `/predict epl`"
    await update.message.reply_text(league_text, parse_mode='Markdown')

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Place a bet"""
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    
    # Check if amount is provided
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify an amount!\n"
            "Example: `/bet 10`",
            parse_mode='Markdown'
        )
        return
    
    try:
        bet_amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount! Please enter a number.",
            parse_mode='Markdown'
        )
        return
    
    # Validate bet
    if bet_amount < Config.MIN_BET:
        await update.message.reply_text(
            f"❌ Minimum bet is {Config.MIN_BET} coin!",
            parse_mode='Markdown'
        )
        return
    
    if bet_amount > Config.MAX_BET:
        await update.message.reply_text(
            f"❌ Maximum bet is {Config.MAX_BET} coins!",
            parse_mode='Markdown'
        )
        return
    
    if bet_amount > user['balance']:
        await update.message.reply_text(
            f"❌ Insufficient balance!\n"
            f"Your balance: ${user['balance']:.2f}\n"
            f"Bet: ${bet_amount:.2f}",
            parse_mode='Markdown'
        )
        return
    
    # Process bet (50/50 chance)
    win = random.random() > 0.5
    
    if win:
        win_amount = bet_amount * 2
        user['balance'] += bet_amount  # Net profit = bet amount (since we win 2x)
        user['total_won'] += bet_amount
        result_text = f"🎉 *YOU WIN!*\n\n"
        result_text += f"💰 Bet: ${bet_amount:.2f}\n"
        result_text += f"💵 Win: ${win_amount:.2f}\n"
        result_text += f"📈 Profit: +${bet_amount:.2f}\n\n"
        result_text += format_balance(user_id)
    else:
        user['balance'] -= bet_amount
        user['total_lost'] += bet_amount
        result_text = f"😢 *YOU LOSE!*\n\n"
        result_text += f"💰 Bet: ${bet_amount:.2f}\n"
        result_text += f"📉 Loss: -${bet_amount:.2f}\n\n"
        result_text += format_balance(user_id)
    
    user['games_played'] += 1
    
    await update.message.reply_text(result_text, parse_mode='Markdown')

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get predictions for a league"""
    if not context.args:
        await update.message.reply_text(
            "📝 *Usage:* `/predict <league>`\n\n"
            "Use `/leagues` to see all options.\n"
            "Example: `/predict epl`",
            parse_mode='Markdown'
        )
        return
    
    league_query = context.args[0].lower()
    
    # Check if league exists
    if league_query not in Config.LEAGUES:
        await update.message.reply_text(
            f"❌ League '{league_query}' not found!\n"
            f"Use `/leagues` to see all options.",
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"🔍 *Fetching predictions for {Config.LEAGUES[league_query]}...*\n"
        f"This may take a moment...",
        parse_mode='Markdown'
    )
    
    try:
        # Fetch odds from API
        url = f"{Config.ODDS_API_BASE_URL}/sports/soccer/odds"
        params = {
            'apiKey': Config.ODDS_API_KEY,
            'region': 'eu',
            'markets': 'h2h'
        }
        
        response = requests.get(url, params=params, timeout=10)
        print(f"📊 API Response: {response.status_code}")
        
        if response.status_code != 200:
            await update.message.reply_text(
                "❌ Could not fetch odds right now.\n"
                "Please try again later.",
                parse_mode='Markdown'
            )
            return
        
        matches = response.json()
        print(f"✅ Found {len(matches)} matches")
        
        # Filter matches for specific league
        league_matches = []
        for match in matches:
            if league_query in match.get('sport_key', '').lower():
                league_matches.append(match)
        
        if not league_matches:
            await update.message.reply_text(
                f"⚠️ No matches found for {Config.LEAGUES[league_query]}.\n"
                f"Check back later!",
                parse_mode='Markdown'
            )
            return
        
        # Format predictions (max 5)
        response_text = f"⚡ *{Config.LEAGUES[league_query]} - Predictions* ⚡\n\n"
        
        for i, match in enumerate(league_matches[:5]):
            try:
                home_team = match.get('home_team', 'Unknown')
                away_team = match.get('away_team', 'Unknown')
                
                # Get best odds
                best_home = 0
                best_away = 0
                best_draw = 0
                
                for bookmaker in match.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':
                            for outcome in market.get('outcomes', []):
                                name = outcome.get('name', '')
                                price = outcome.get('price', 0)
                                if name == home_team:
                                    best_home = max(best_home, price)
                                elif name == away_team:
                                    best_away = max(best_away, price)
                                elif name == 'Draw':
                                    best_draw = max(best_draw, price)
                
                # Calculate predictions
                if best_home > 0 and best_away > 0 and best_draw > 0:
                    home_prob = (1 / best_home) * 100
                    draw_prob = (1 / best_draw) * 100
                    away_prob = (1 / best_away) * 100
                    
                    total = home_prob + draw_prob + away_prob
                    home_prob = (home_prob / total) * 100
                    draw_prob = (draw_prob / total) * 100
                    away_prob = (away_prob / total) * 100
                    
                    # Determine prediction
                    outcomes = [
                        ('Home Win', home_prob),
                        ('Draw', draw_prob),
                        ('Away Win', away_prob)
                    ]
                    outcomes.sort(key=lambda x: x[1], reverse=True)
                    
                    response_text += f"*{home_team} vs {away_team}*\n"
                    response_text += f"🔮 *Prediction:* {outcomes[0][0]}\n"
                    response_text += f"📊 *Confidence:* {outcomes[0][1] - outcomes[1][1]:.1f}%\n"
                    response_text += f"💰 *Best Odds:* H:{best_home:.2f} D:{best_draw:.2f} A:{best_away:.2f}\n\n"
                    
            except Exception as e:
                print(f"Error formatting match: {e}")
                continue
        
        if len(response_text) > 4000:
            parts = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(response_text, parse_mode='Markdown')
        
    except Exception as e:
        print(f"Error in predict: {e}")
        await update.message.reply_text(
            "❌ An error occurred. Please try again later.",
            parse_mode='Markdown'
        )

# ==================== MAIN ====================

def main():
    """Start the bot"""
    try:
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("balance", balance_command))
        application.add_handler(CommandHandler("leagues", leagues_command))
        application.add_handler(CommandHandler("bet", bet_command))
        application.add_handler(CommandHandler("predict", predict_command))
        
        # Start the bot
        logger.info("🚀 Starting PariBot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
