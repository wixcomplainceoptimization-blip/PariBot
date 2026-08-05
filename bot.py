import logging
import sys
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "🎮 *Features:*\n"
        "• Betting game with real balance\n"
        "• 50/50 win chance\n"
        "• Track your wins & losses\n"
        "• Beautiful Mini App UI\n\n"
        f"💰 *Starting balance:* {Config.INITIAL_BALANCE} coins\n"
        f"🎯 *Min bet:* {Config.MIN_BET} coin\n"
        f"🎯 *Max bet:* {Config.MAX_BET} coins\n\n"
        "Click the button below to start!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 *PariBot Help*\n\n"
        "*How to play:*\n"
        "1. Click 'Open PariBot'\n"
        "2. Enter your bet amount\n"
        "3. Click Spin!\n"
        "4. 50/50 chance to win!\n\n"
        "*Commands:*\n"
        "/start - Open the bot\n"
        "/help - Show this help",
        parse_mode='Markdown'
    )

def main():
    try:
        app = Application.builder().token(Config.BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        
        logger.info("🚀 Starting PariBot...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
