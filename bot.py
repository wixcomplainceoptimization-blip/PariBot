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
        
        response = "📊
