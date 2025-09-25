import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Solana RPC Configuration
SOLANA_RPC_HTTP_URL = os.getenv("SOLANA_RPC_HTTP_URL", "https://api.mainnet-beta.solana.com")
SOLANA_RPC_WS_URL = os.getenv("SOLANA_RPC_WS_URL", "wss://api.mainnet-beta.solana.com")

# Wallet Configuration (encrypted)
WALLET_PRIVATE_KEY = os.getenv("WALLET_PRIVATE_KEY")  # Will be decrypted at runtime

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("7983726333:AAEbIGhlQQ96HgIh18tlwJgxCLrqj_cqZD8")
TELEGRAM_ADMIN_ID = os.getenv("3336273897")

# Bot Configuration
SNIPE_TIMEOUT = int(os.getenv("SNIPE_TIMEOUT", "30"))
MAX_SLIPPAGE = float(os.getenv("MAX_SLIPPAGE", "100"))
CHECK_RUG = os.getenv("CHECK_RUG", "True").lower() == "true"
MIN_LIQUIDITY = float(os.getenv("MIN_LIQUIDITY", "1.0"))  # SOL
MAX_BUY_AMOUNT = float(os.getenv("MAX_BUY_AMOUNT", "50"))  # SOL

# Program IDs
RAYDIUM_AMM_PROGRAM_ID = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
RAYDIUM_CLMM_PROGRAM_ID = "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"
PUMP_FUN_PROGRAM_ID = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

# API URLs
JUPITER_API_URL = "https://quote-api.jup.ag/v6"
JUPITER_PRICE_API_URL = "https://price.jup.ag/v4"
DEXSCREENER_API_URL = "https://api.dexscreener.com/latest/dex"

# Monitoring
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "5"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Security
ENCRYPTION_KEY = os.getenv("Crypt0_Kingzs") or "default-key-please-change-in-production"

# Paths
LOG_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"
LOG_DIR.mkdir(exist_ok=True)
CACHE_DIR.mkdir(exist_ok=True)

# Database (for persistent state)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/bot.db")

