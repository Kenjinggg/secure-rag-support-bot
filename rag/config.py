"""All settings in one place. Override any of them in your .env file."""
import os

from dotenv import load_dotenv

load_dotenv()

# Where the knowledge base lives
DATA_DIR = os.getenv("DATA_DIR", "data")
DB_DIR = os.getenv("DB_DIR", "chroma_db")
COLLECTION = os.getenv("COLLECTION", "store_docs")

# Free local embedding model (downloads ~90 MB on first run)
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

# LLM: switch provider with one line in .env ("anthropic" or "openai")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-haiku-5-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "500"))

# Chunking (characters)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Retrieval
TOP_K = int(os.getenv("TOP_K", "4"))
# If even the best chunk scores below this, we answer "I don't know"
# without calling the LLM at all (saves money, prevents made-up answers).
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.30"))

# Public demo limits (web app only). Anyone with the link spends your API
# budget, so cap questions per visitor and per day across all visitors.
MAX_QUESTIONS_PER_SESSION = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "15"))
MAX_QUESTIONS_PER_DAY = int(os.getenv("MAX_QUESTIONS_PER_DAY", "300"))

# Branding for the demo store
STORE_NAME = os.getenv("STORE_NAME", "Nusa Threads")
SUPPORT_EMAIL = os.getenv("SUPPORT_EMAIL", "support@nusathreads.example")
