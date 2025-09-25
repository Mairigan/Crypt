import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID
from bot.sniper_bot import sniper_bot

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()

    def setup_handlers(self):
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("balance", self.balance))
        self.application.add_handler(CommandHandler("auto_snipe", self.auto_snipe))
        self.application.add_handler(CommandHandler("manual_snipe", self.manual_snipe))
        self.application.add_handler(CommandHandler("monitor", self.monitor))
        self.application.add_handler(CommandHandler("settings", self.settings))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        user = update.effective_user
        if str(user.id) != TELEGRAM_ADMIN_ID:
            await update.message.reply_text("Unauthorized access.")
            return
            
        keyboard = [['/status', '/balance'], ['/auto_snipe', '/manual_snipe'], ['/monitor', '/settings']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            f"Hello {user.mention_markdown_v2()}\! 🤖\n\n"
            "Welcome to your Solana Sniper Bot\! Use the commands below to get started\.",
            reply_markup=reply_markup,
            parse_mode='MarkdownV2'
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /help is issued."""
        help_text = """
        *Available Commands:*
        /start - Start the bot
        /help - Show this help message
        /status - Check bot status
        /balance - Check wallet balance
        /auto_snipe - Toggle auto sniping on/off
        /manual_snipe <mint_address> - Manually snipe a token
        /monitor <mint_address> - Monitor a token's price
        /settings - Configure bot settings
        
        *Usage Examples:*
        `/manual_snipe CwP5d...` - Snipe a specific token
        `/monitor CwP5d...` - Monitor a token's price
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send bot status information."""
        status = await sniper_bot.get_status()
        await update.message.reply_text(status, parse_mode='Markdown')

    async def balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Check wallet balance."""
        balance = await sniper_bot.get_balance()
        await update.message.reply_text(f"Wallet balance: {balance} SOL")

    async def auto_snipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle auto sniping on/off."""
        if sniper_bot.auto_snipe_enabled:
            sniper_bot.auto_snipe_enabled = False
            await update.message.reply_text("Auto snipe disabled.")
        else:
            sniper_bot.auto_snipe_enabled = True
            await update.message.reply_text("Auto snipe enabled.")

    async def manual_snipe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manually snipe a token by mint address."""
        if not context.args:
            await update.message.reply_text("Please provide a mint address. Usage: /manual_snipe <mint_address>")
            return
            
        mint_address = context.args[0]
        await update.message.reply_text(f"Attempting to snipe {mint_address}...")
        
        # Execute the snipe in a separate task to avoid blocking
        asyncio.create_task(sniper_bot.manual_snipe(mint_address, update))

    async def monitor(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Monitor a token's price."""
        if not context.args:
            await update.message.reply_text("Please provide a mint address. Usage: /monitor <mint_address>")
            return
            
        mint_address = context.args[0]
        asyncio.create_task(sniper_bot.monitor_token(mint_address, update))

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configure bot settings."""
        # This would typically show a keyboard with configurable options
        await update.message.reply_text("Settings menu is under development.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages."""
        text = update.message.text
        await update.message.reply_text(f"I received your message: {text}")

    async def send_message(self, chat_id, text):
        """Send a message to a specific chat."""
        await self.application.bot.send_message(chat_id=chat_id, text=text)

    def run(self):
        """Start the bot."""
        self.application.run_polling()

# Global instance
telegram_bot = TelegramBot()
