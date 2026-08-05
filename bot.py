import logging
import sys
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Get bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found in environment variables!")
    sys.exit(1)

# Simple welcome message
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"⚡ *Welcome to PariBot, {user.first_name}!* ⚡\n\n"
        "🎲 I'm a simple betting bot!\n\n"
        "📋 *Commands:*\n"
        "/start - Show this message\n"
        "/help - Show help\n"
        "/balance - Check your balance\n"
        "/bet <amount> - Place a bet\n\n"
        "⚠️ *Coming soon:* Mini App version!",
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 *PariBot Help*\n\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/balance - Check your balance\n"
        "/bet <amount> - Bet coins (50/50 chance)\n\n"
        "*Example:* `/bet 10`",
        parse_mode='Markdown'
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 *Your Balance*\n\n"
        "Current balance: 100 coins\n"
        "Minimum bet: 1 coin\n"
        "Maximum bet: 100 coins",
        parse_mode='Markdown'
    )

async def bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Please specify amount!\n"
            "Example: `/bet 10`",
            parse_mode='Markdown'
        )
        return
    
    try:
        amount = float(context.args[0])
        if amount < 1 or amount > 100:
            await update.message.reply_text(
                "❌ Bet must be between 1 and 100 coins!",
                parse_mode='Markdown'
            )
            return
        
        # Simple response (no real betting yet)
        await update.message.reply_text(
            f"✅ You bet {amount} coins!\n"
            f"🎲 Spinning...\n\n"
            f"💡 This is a demo. Full betting coming soon!",
            parse_mode='Markdown'
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount! Enter a number.",
            parse_mode='Markdown'
        )

def main():
    try:
        logger.info("🚀 Starting PariBot...")
        logger.info(f"🔑 Token: {BOT_TOKEN[:10]}...")
        
        # Create application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("balance", balance_command))
        app.add_handler(CommandHandler("bet", bet_command))
        
        # Start the bot
        logger.info("✅ Bot is running!")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
