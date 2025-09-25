import asyncio
import signal
import sys
from bot.telegram_bot import telegram_bot
from bot.sniper_bot import sniper_bot

class SniperBotApp:
    def __init__(self):
        self.is_running = False
        
    async def initialize(self):
        """Initialize the application components."""
        try:
            # Initialize components
            print("Initializing Solana Sniper Bot...")
            
            # Test connection to Solana
            balance = await sniper_bot.get_balance()
            print(f"Wallet balance: {balance} SOL")
            
            # Start monitoring for new pools
            await sniper_bot.start_monitoring()
            
            print("Application initialized successfully")
            return True
            
        except Exception as e:
            print(f"Failed to initialize application: {e}")
            return False
    
    async def run(self):
        """Run the application."""
        if not await self.initialize():
            return
        
        self.is_running = True
        
        # Start Telegram bot in a separate task
        telegram_task = asyncio.create_task(self.run_telegram_bot())
        
        # Main loop
        try:
            while self.is_running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("Application was cancelled")
        finally:
            await self.shutdown()
    
    async def run_telegram_bot(self):
        """Run the Telegram bot."""
        try:
            await telegram_bot.application.initialize()
            await telegram_bot.application.start()
            await telegram_bot.application.updater.start_polling()
            print("Telegram bot is running")
            
            # Keep the task running
            while self.is_running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Telegram bot error: {e}")
        finally:
            if telegram_bot.application.updater:
                await telegram_bot.application.updater.stop()
            if telegram_bot.application:
                await telegram_bot.application.stop()
            if telegram_bot.application.updater:
                await telegram_bot.application.updater.shutdown()
    
    async def shutdown(self, signal=None):
        """Cleanup resources."""
        if signal:
            print(f"Received exit signal {signal.name}...")
        
        self.is_running = False
        print("Shutting down application...")
        
        await sniper_bot.close()
        
        print("Application shutdown complete")

def handle_exception(loop, context):
    """Handle uncaught exceptions."""
    msg = context.get("exception", context["message"])
    print(f"Uncaught exception: {msg}")
    print("Shutting down...")
    asyncio.create_task(app.shutdown())

async def main():
    """Main application entry point."""
    global app
    app = SniperBotApp()
    
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(app.shutdown(s)))
    
    # Set exception handler
    loop.set_exception_handler(handle_exception)
    
    try:
        await app.run()
    except Exception as e:
        print(f"Error running application: {e}")
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Shutting down...")
