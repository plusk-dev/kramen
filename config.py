import os
from redis.asyncio import Redis
from qdrant_client import QdrantClient

# Fetch environment variables with default values
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")
# if DATABASE_URL == "":
DATABASE_URL = "sqlite:///dev.db"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

DENSE_EMBEDDING_MODEL = os.getenv("DENSE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SPARSE_EMBEDDING_MODEL = os.getenv("SPARSE_EMBEDDING_MODEL", "bm25")
LATE_EMBEDDING_MODEL = os.getenv("LATE_EMBEDDING_MODEL", "colbertv2.0")

DEFAULT_RATE_LIMIT = 1000

# LLM API Key mapping - maps LLM names to their API keys
LLM_API_KEYS = {
    "gpt-4o-mini": os.getenv("OPENAI_API_KEY", ""),
    "openai/gpt-4o": os.getenv("OPENAI_API_KEY", ""),
    "openai/gpt-4.1": os.getenv("OPENAI_API_KEY", ""),
    "openai/gpt-3.5-turbo": os.getenv("OPENAI_API_KEY", ""),
    "openai/gpt-4o-mini": os.getenv("OPENAI_API_KEY", ""),
    "claude-3-opus": os.getenv("ANTHROPIC_API_KEY", ""),
    "claude-3-sonnet": os.getenv("ANTHROPIC_API_KEY", ""),
    "claude-3-haiku": os.getenv("ANTHROPIC_API_KEY", ""),
    "google/gemini-pro": os.getenv("GOOGLE_API_KEY", ""),
    "llama-2": os.getenv("META_API_KEY", ""),
    # Add more LLM mappings as needed
}

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,  # e.g. "http://localhost:6333" or your cloud URL,
    api_key=QDRANT_API_KEY
)

redis_client = Redis.from_url(REDIS_URL)

# Default LLM configuration
DEFAULT_LLM = "openai/gpt-4.1"

def configure_default_dspy():
    """Configure DSPy with the default LLM model."""
    import dspy
    
    api_key = LLM_API_KEYS.get(DEFAULT_LLM, "")
    if not api_key:
        raise ValueError(f"No API key found for default LLM: {DEFAULT_LLM}")
    
    lm = dspy.LM(
        model=DEFAULT_LLM,
        api_key=api_key
    )
    dspy.configure(lm=lm)
