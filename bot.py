import logging
import sys
import os
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with WebApp button"""
    user = update.effective_user
    
    button = KeyboardButton(
        "🎲 Open PariBot",
        web_app=WebAppInfo(url=Config.WEBAPP_URL)
    )
    
    reply_markup = ReplyKeyboardMarkup(
        [[button]],
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        f"⚡ *Welcome to PariBot, {user.first_name}!* ⚡\n\n"
        "I'm your gaming companion with a full WebApp experience.\n\n"
        "🎮 *Features:*\n"
        "• Real-time balance tracking\n"
        "• Win/Lose betting games\n"
        "• Game history tracking\n"
        "• Beautiful UI inside Telegram\n\n"
        "💰 *Starting balance:* 100 coins\n"
        "🎯 *Min bet:* 1 coin\n"
        "🎯 *Max bet:* 100 coins\n\n"
        "Click the button below to start playing!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message"""
    await update.message.reply_text(
        "🎮 *PariBot Help*\n\n"
        "*How to play:*\n"
        "1. Click 'Open PariBot' button\n"
        "2. Enter your bet amount\n"
        "3. Click Spin!\n"
        "4. Win or lose - it's all in the game!\n\n"
        "*Rules:*\n"
        "💰 Starting balance: 100 coins\n"
        "🎯 Min bet: 1 coin\n"
        "🎯 Max bet: 100 coins\n"
        "🎲 50/50 win chance\n\n"
        "*Commands:*\n"
        "/start - Open the bot\n"
        "/help - Show this help\n"
        "/balance - Check your balance",
        parse_mode='Markdown'
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check balance"""
    await update.message.reply_text(
        "💰 Your balance is shown in the WebApp.\n"
        "Open PariBot to see your current balance!",
        parse_mode='Markdown'
    )

def main():
    """Start the bot"""
    try:
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("balance", balance_command))
        
        logger.info("🚀 Starting PariBot Telegram Bot...")
        logger.info(f"📱 WebApp URL: {Config.WEBAPP_URL}")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
