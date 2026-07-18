#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import traceback
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

from config import Config
from odds_api import OddsAPI
from database import Database
from utils import Utils

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('paribot.log')
    ]
)
logger = logging.getLogger(__name__)

# ==================== HEALTHCHECK SERVER ====================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def run_healthcheck_server():
    try:
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🏥 Healthcheck server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Healthcheck server error: {e}")

# ==================== INITIALIZATION ====================
odds_api = OddsAPI()
db = Database()

# ==================== CONSTANTS ====================
SPORT_SELECTION, LEAGUE_SELECTION, BET_AMOUNT = range(3)

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    logger.error(traceback.format_exc())
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Something went wrong. Please try again later."
            )
    except:
        pass

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with user registration"""
    user = update.effective_user
    
    # Register user in database
    db.add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    welcome_message = f"""
🎯 *Welcome to PariBot!* 🎯

Hi {user.first_name}! I'm your advanced betting assistant with real-time predictions.

🔮 *What I can do:*
• Multi-sport predictions (⚽🏀🎾⚾)
• Live odds from top bookmakers
• Value bet detection
• Betting history tracking
• Price alerts & notifications
• Spread & totals analysis

📋 *Commands:*
/predict - Get top predictions
/predict <sport> - Predictions for specific sport
/odds <league> - Get odds for a league
/myleagues - Set your favorite leagues
/history - View your betting history
/alerts - Set price alerts
/sports - List all supported sports
/help - Help message
/about - About PariBot

🔍 *Examples:*
`/predict football`
`/odds premier`
`/alerts`

⚠️ *Disclaimer:* Always bet responsibly!
"""
    
    keyboard = [
        [
            InlineKeyboardButton("🔮 Get Predictions", callback_data="predict"),
            InlineKeyboardButton("⚽ Sports", callback_data="sports")
        ],
        [
            InlineKeyboardButton("💰 Value Bets", callback_data="value_bets"),
            InlineKeyboardButton("📊 History", callback_data="history")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command"""
    help_text = """
🎯 *PariBot Help Center*

*Basic Commands:*
/predict - Get top predictions
/predict <sport> - Predictions for specific sport
/odds <league> - Get odds for a league
/myleagues - Manage your favorite leagues
/sports - List supported sports

*Advanced Features:*
/history - View your betting history
/alerts - Set price alerts
/stats - View prediction statistics

*Sports Available:*
• Football (⚽)
• Basketball (🏀)
• Tennis (🎾)
• Baseball (⚾)

*Quick Usage:*
`/predict football` - Get football predictions
`/odds epl` - Get EPL odds
`/alerts` - Set alerts for odds changes

*Responsible Gaming:*
Set limits, bet responsibly, never chase losses!
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """About command"""
    about_text = """
⚡ *About PariBot* ⚡

🤖 *Version:* 2.0.0
📅 *Released:* 2026
🏆 *Features:* Multi-sport, AI predictions, value detection

*Key Features:*
• Real-time odds from multiple bookmakers
• AI-powered probability analysis
• Value bet detection
• Multiple sports support
• User preferences & history
• Price alerts

*Data Sources:*
• The Odds API

*Responsible Gaming:*
For entertainment only. Please bet responsibly.

💡 *Pro Tip:* Use `/alerts` to get notified when odds change!
"""
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def sports_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all supported sports"""
    sports_text = "🏟️ *Supported Sports*\n\n"
    
    for sport in Config.SPORTS:
        emoji = Config.SPORT_EMOJIS.get(sport, '⚽')
        sports_text += f"{emoji} {sport.capitalize()}\n"
        sports_text += f"   Use: `/predict {sport}`\n\n"
    
    sports_text += "💡 *Tip:* Add `-league` to get league-specific predictions"
    await update.message.reply_text(sports_text, parse_mode='Markdown')

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get predictions with optional sport filter"""
    try:
        # Check if sport specified
        sport_filter = None
        if context.args:
            sport_arg = ' '.join(context.args).lower()
            sport_filter = Utils.extract_sport(sport_arg)
        
        await update.message.reply_text("🔍 *Analyzing matches... Please wait*", parse_mode='Markdown')
        
        # Fetch all matches
        matches = odds_api.get_all_sports_odds()
        
        if not matches:
            await update.message.reply_text("❌ No matches found at the moment.")
            return
        
        # Get predictions
        predictions = odds_api.get_predictions(matches, sport_filter)
        
        if not predictions:
            await update.message.reply_text("⚠️ No predictions available. Try another sport or check back later!")
            return
        
        # Format response
        response = f"⚡ *Top Predictions* ⚡\n"
        if sport_filter:
            response += f"🎯 *Sport:* {sport_filter.capitalize()}\n"
        response += "\n"
        
        for i, pred in enumerate(predictions[:Config.MAX_PREDICTIONS_DISPLAY]):
            response += odds_api.format_prediction(pred)
            if i < Config.MAX_PREDICTIONS_DISPLAY - 1:
                response += "\n" + "─" * 35 + "\n"
        
        # Split long messages
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in predict_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def odds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get odds for a specific league"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📝 *Usage:* `/odds <league>`\n\n"
                "Examples:\n"
                "`/odds premier` - Premier League\n"
                "`/odds la liga` - La Liga\n"
                "`/odds nba` - NBA\n\n"
                "Use `/sports` to see all options.",
                parse_mode='Markdown'
            )
            return
        
        league_query = ' '.join(context.args).lower()
        league_key = Utils.extract_league(league_query)
        
        if not league_key:
            await update.message.reply_text(
                f"❌ League '{league_query}' not found.\n\nUse `/sports` to see all leagues.",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(f"🔍 *Fetching odds for {Config.LEAGUE_NAMES.get(league_key, league_key)}...*", parse_mode='Markdown')
        
        matches = odds_api.get_all_sports_odds()
        
        if not matches:
            await update.message.reply_text("❌ No matches found.")
            return
        
        # Filter matches for specific league
        league_matches = [m for m in matches if league_key in m.get('sport_key', '')]
        
        if not league_matches:
            await update.message.reply_text(f"⚠️ No current matches found.")
            return
        
        predictions = odds_api.get_predictions(league_matches)
        
        if not predictions:
            await update.message.reply_text("⚠️ No odds available.")
            return
        
        response = f"⚡ *{Config.LEAGUE_NAMES.get(league_key, league_key)} - Odds* ⚡\n\n"
        for i, pred in enumerate(predictions[:3]):
            response += odds_api.format_prediction(pred)
            if i < len(predictions) - 1:
                response += "\n" + "─" * 35 + "\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in odds_command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def myleagues_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage favorite leagues"""
    keyboard = [
        [
            InlineKeyboardButton("⚽ Premier League", callback_data="set_league_premier"),
            InlineKeyboardButton("🇪🇸 La Liga", callback_data="set_league_laliga")
        ],
        [
            InlineKeyboardButton("🇮🇹 Serie A", callback_data="set_league_seriea"),
            InlineKeyboardButton("🏀 NBA", callback_data="set_league_nba")
        ],
        [
            InlineKeyboardButton("🎾 ATP", callback_data="set_league_atp"),
            InlineKeyboardButton("⚾ MLB", callback_data="set_league_mlb")
        ],
        [
            InlineKeyboardButton("❌ Clear Preferences", callback_data="clear_preferences")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚙️ *Select your favorite leagues*\n\n"
        "I'll prioritize these in predictions!",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View betting history"""
    try:
        history = db.get_recent_predictions(limit=5)
        
        if not history:
            await update.message.reply_text("📊 No history yet. Start making predictions!")
            return
        
        response = "📊 *Your Recent Activity*\n\n"
        for i, item in enumerate(history, 1):
            response += f"{i}. {item.home_team} vs {item.away_team}\n"
            response += f"   Prediction: {item.prediction} (Confidence: {item.confidence:.1f}%)\n"
            response += f"   Odds: {item.home_odds:.2f} | {item.draw_odds:.2f} | {item.away_odds:.2f}\n\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in history_command: {e}")
        await update.message.reply_text("❌ Error fetching history.")

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set up price alerts"""
    alert_message = """
🔔 *Price Alerts*

Set alerts for odds changes!

*How it works:*
1. Choose a match
2. Set target odds
3. Get notified when odds reach your target

💡 *Coming soon:* Full alert system with notifications!

*Currently supported:*
• Manual check with `/predict`
• High-confidence predictions highlighted

Stay tuned for real-time alerts! 🚀
"""
    await update.message.reply_text(alert_message, parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show prediction statistics"""
    stats_message = """
📊 *PariBot Statistics*

🎯 *Available Stats:*
• Total predictions made today
• Highest confidence predictions
• Most profitable leagues
• Value bets identified

*Coming soon:* Historical accuracy tracking!

📈 *Current Performance:*
• Active matches tracked: Looking for matches...
• Supported leagues: 12+
• Sports available: 4

Use `/predict` to start analyzing! 🚀
"""
    await update.message.reply_text(stats_message, parse_mode='Markdown')

# ==================== CALLBACK HANDLERS ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "predict":
        await predict_command(update, context)
    
    elif data == "sports":
        await sports_command(update, context)
    
    elif data == "value_bets":
        await query.edit_message_text(
            "💰 *Value Bets*\n\n"
            "Finding best value bets...\n"
            "Check `/predict` for top picks!",
            parse_mode='Markdown'
        )
    
    elif data == "history":
        await history_command(update, context)
    
    elif data.startswith("set_league_"):
        league = data.replace("set_league_", "")
        user = update.effective_user
        
        # Map short codes to full names
        league_map = {
            'premier': 'england_premier_league',
            'laliga': 'spain_la_liga',
            'seriea': 'italy_serie_a',
            'nba': 'usa_nba',
            'atp': 'atp',
            'mlb': 'mlb'
        }
        
        league_key = league_map.get(league, league)
        
        db.update_user_preferences(user.id, league=league_key)
        
        league_name = Config.LEAGUE_NAMES.get(league_key, league_key)
        await query.edit_message_text(
            f"✅ Favorite league set to {league_name}!\n"
            f"Use `/predict` to get predictions!",
            parse_mode='Markdown'
        )
    
    elif data == "clear_preferences":
        user = update.effective_user
        db.update_user_preferences(user.id, sport=None, league=None)
        await query.edit_message_text(
            "✅ Preferences cleared!\n"
            "Use `/myleagues` to set new favorites.",
            parse_mode='Markdown'
        )

# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages"""
    text = update.message.text
    
    # Check for sport mention
    sport = Utils.extract_sport(text)
    if sport:
        context.args = [sport]
        await predict_command(update, context)
        return
    
    # Default response
    response = """
🤖 *PariBot*

Try these commands:
• `/predict` - Get predictions
• `/predict football` - Football predictions
• `/odds epl` - Premier League odds
• `/myleagues` - Set favorites
• `/help` - All commands
"""
    await update.message.reply_text(response, parse_mode='Markdown')

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot"""
    try:
        # Start healthcheck server
        health_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
        health_thread.start()
        
        logger.info("🚀 Starting PariBot...")
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("sports", sports_command))
        application.add_handler(CommandHandler("predict", predict_command))
        application.add_handler(CommandHandler("odds", odds_command))
        application.add_handler(CommandHandler("myleagues", myleagues_command))
        application.add_handler(CommandHandler("history", history_command))
        application.add_handler(CommandHandler("alerts", alerts_command))
        application.add_handler(CommandHandler("stats", stats_command))
        
        # Add callback handler
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Add message handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start the bot
        logger.info("✅ PariBot is running!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
