#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys
import os
import traceback
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Fix for Python 3.13 compatibility
import telegram
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import Config
from odds_api import OddsAPI
from utils import Utils

# ==================== LOGGING ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('betbolt.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize API handler
odds_api = OddsAPI()

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
    """Run a simple HTTP server for Railway healthchecks"""
    try:
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"🏥 Healthcheck server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Healthcheck server error: {e}")

# ==================== ERROR HANDLER ====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and send message to user"""
    logger.error(f"Update {update} caused error {context.error}")
    logger.error(traceback.format_exc())
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Sorry, something went wrong. Please try again later.\n"
                "The error has been logged and will be fixed soon."
            )
    except:
        pass

# ==================== COMMAND HANDLERS ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message when /start is issued"""
    try:
        user = update.effective_user
        welcome_message = f"""
⚡ *Welcome to BetBolt!* ⚡

Hi {user.first_name}! I'm your AI betting assistant.

📋 *Available Commands:*
/predict - Get top predictions
/odds <league> - Get odds for specific league
/leagues - Show supported leagues
/help - Show this help message
/about - About BetBolt

⚠️ *Disclaimer:* Always bet responsibly!
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text("❌ Error starting bot. Please try /help")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    try:
        help_text = """
⚡ *BetBolt Help Center* ⚡

*Commands:*
/predict - Get top 3 predictions
/odds <league> - Get odds for specific league
/leagues - List all supported leagues
/start - Welcome message
/help - Show this help
/about - About BetBolt

*Supported Leagues:*
• Premier League (EPL)
• La Liga
• Serie A
• Bundesliga
• Ligue 1
• Eredivisie
• Primeira Liga
• Brasileirão

*How to use:*
Type `/odds epl` to see Premier League odds
Type `/predict` for top picks

*Disclaimer:*
Always gamble responsibly and within your limits.
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help_command: {e}")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send about message"""
    try:
        about_text = """
⚡ *About BetBolt* ⚡

🤖 *Version:* 1.0.0
📅 *Released:* 2026

*Features:*
• Real-time odds from multiple bookmakers
• AI-powered probability analysis
• Multiple league support
• Confidence scoring system

*Data Sources:*
• The Odds API

*Responsible Gaming:*
BetBolt is designed for entertainment purposes only.
Please bet responsibly.
"""
        await update.message.reply_text(about_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in about_command: {e}")

async def leagues_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show supported leagues"""
    try:
        league_text = "⚽ *Supported Leagues*\n\n"
        for key, name in Config.LEAGUE_NAMES.items():
            league_text += f"• {name}\n"
            league_text += f"  (use: `/odds {key.replace('_', ' ')}`)\n\n"
        
        league_text += "\n💡 *Tip:* Try `/odds premier` for EPL odds!"
        await update.message.reply_text(league_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in leagues_command: {e}")

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top predictions"""
    try:
        await update.message.reply_text("🔍 *Analyzing matches... Please wait*", parse_mode='Markdown')
        
        matches = odds_api.get_odds()
        
        if not matches:
            await update.message.reply_text(
                "❌ No matches found at the moment.\n\n"
                "Possible reasons:\n"
                "• No live matches right now\n"
                "• API key may be invalid\n"
                "• Rate limit exceeded\n\n"
                "Please try again later."
            )
            return
        
        predictions = odds_api.get_predictions(matches)
        
        if not predictions:
            await update.message.reply_text(
                "⚠️ No predictions available right now.\n"
                "This could be because:\n"
                "• Matches found but no odds data\n"
                "• Bookmaker data unavailable\n\n"
                "Try again later!"
            )
            return
        
        response = "⚡ *Top Predictions* ⚡\n\n"
        for i, pred in enumerate(predictions[:Config.MAX_PREDICTIONS_DISPLAY]):
            response += odds_api.format_prediction_message(pred, i)
            if i < Config.MAX_PREDICTIONS_DISPLAY - 1:
                response += "\n" + "─" * 30 + "\n"
        
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in predict_command: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ An error occurred while fetching predictions.\n"
            "Please try again later.\n\n"
            f"Error: {str(e)[:100]}"
        )

async def odds_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get odds for a specific league"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📝 *Usage:* `/odds <league>`\n\n"
                "Example: `/odds premier` or `/odds epl`\n\n"
                "Use `/leagues` to see all options.",
                parse_mode='Markdown'
            )
            return
        
        league_query = ' '.join(context.args).lower()
        
        league_key = None
        for key, name in Config.LEAGUE_NAMES.items():
            if league_query in key.lower() or league_query in name.lower():
                league_key = key
                break
        
        if not league_key:
            await update.message.reply_text(
                f"❌ League '{league_query}' not found.\n\n"
                f"Use `/leagues` to see all supported leagues.",
                parse_mode='Markdown'
            )
            return
        
        await update.message.reply_text(
            f"🔍 *Fetching odds for {Config.LEAGUE_NAMES[league_key]}...*\n"
            f"This may take a moment...",
            parse_mode='Markdown'
        )
        
        matches = odds_api.get_odds()
        
        if not matches:
            await update.message.reply_text(
                "❌ No matches found at the moment.\n"
                "Please try again later."
            )
            return
        
        league_matches = [m for m in matches if league_key in m.get('sport_key', '')]
        
        if not league_matches:
            await update.message.reply_text(
                f"⚠️ No current matches found for {Config.LEAGUE_NAMES[league_key]}.\n"
                f"They might be playing later today."
            )
            return
        
        predictions = odds_api.get_predictions(league_matches)
        
        if not predictions:
            await update.message.reply_text(
                f"⚠️ No odds available for these matches.\n"
                f"Try again closer to match time."
            )
            return
        
        response = f"⚡ *{Config.LEAGUE_NAMES[league_key]} - Odds & Predictions* ⚡\n\n"
        for i, pred in enumerate(predictions[:3]):
            response += odds_api.format_prediction_message(pred, i)
            if i < len(predictions) - 1:
                response += "\n" + "─" * 30 + "\n"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in odds_command: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "❌ An error occurred.\n"
            "Please try again later."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle non-command messages"""
    try:
        text = update.message.text
        
        if Utils.is_valid_command(text):
            return
        
        response = """
🤖 *BetBolt Bot*

I didn't understand that. Try using:
• /predict - Get predictions
• /odds <league> - Get odds for a league
• /leagues - Show supported leagues
• /help - Get help
"""
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")

# ==================== MAIN FUNCTION ====================

def main():
    """Start the bot with error handling"""
    try:
        # Start healthcheck server in a separate thread
        health_thread = threading.Thread(target=run_healthcheck_server, daemon=True)
        health_thread.start()
        
        # Print Python version for debugging
        logger.info(f"🐍 Python version: {sys.version}")
        logger.info(f"📦 Telegram version: {telegram.__version__}")
        logger.info(f"🔑 API Key present: {bool(Config.ODDS_API_KEY)}")
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Add error handler
        application.add_error_handler(error_handler)
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("about", about_command))
        application.add_handler(CommandHandler("leagues", leagues_command))
        application.add_handler(CommandHandler("predict", predict_command))
        application.add_handler(CommandHandler("odds", odds_command))
        
        # Handle messages
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start the bot
        logger.info("🚀 Starting BetBolt bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
