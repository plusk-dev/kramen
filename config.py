import os
from qdrant_client import QdrantClient

# Fetch environment variables with default values
REDIS_URL = os.getenv("REDIS_URL", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DATABASE_URL = os.getenv("DATABASE_URL", "dev.db")
JWT_SECRET = os.getenv("JWT_SECRET", "cocomelon")
JWT_EXPIRY_DAYS = int(os.getenv("JWT_EXPIRY_DAYS", 2))

DENSE_EMBEDDING_MODEL = os.getenv("DENSE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SPARSE_EMBEDDING_MODEL = os.getenv("SPARSE_EMBEDDING_MODEL", "bm25")
LATE_EMBEDDING_MODEL = os.getenv("LATE_EMBEDDING_MODEL", "colbertv2.0")

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,  # e.g. "http://localhost:6333" or your cloud URL
)