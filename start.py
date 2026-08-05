import multiprocessing
import sys
import os
import time
import subprocess

if __name__ == '__main__':
    # Start Flask backend
    print("🚀 Starting PariBot...")
    print("📡 Starting Flask server...")
    
    # Run Flask in a separate process
    flask_process = subprocess.Popen(
        [sys.executable, 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for Flask to start
    time.sleep(2)
    
    print("🤖 Starting Telegram bot...")
    # Run Telegram bot
    bot_process = subprocess.Popen(
        [sys.executable, 'bot.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("✅ PariBot is running!")
    print("📱 Open Telegram and send /start to your bot")
    
    # Keep running
    try:
        flask_process.wait()
        bot_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down PariBot...")
        flask_process.terminate()
        bot_process.terminate()
