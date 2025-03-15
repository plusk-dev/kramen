import os
from redis.asyncio import Redis
from qdrant_client import QdrantClient

# Fetch environment variables with default values
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")
if DATABASE_URL == "":
    DATABASE_URL = "sqlite:///dev.db"
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
JWT_SECRET = os.getenv("JWT_SECRET", "cocomelon")
JWT_EXPIRY_DAYS = int(os.getenv("JWT_EXPIRY_DAYS", 2))

DENSE_EMBEDDING_MODEL = os.getenv("DENSE_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SPARSE_EMBEDDING_MODEL = os.getenv("SPARSE_EMBEDDING_MODEL", "bm25")
LATE_EMBEDDING_MODEL = os.getenv("LATE_EMBEDDING_MODEL", "colbertv2.0")

KRAMEN_PRODUCT_ID = os.getenv("PRODUCT_ID", "prod_RtAaDut7sjXW4w")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_51PXtInINlb77fuyVbfH0uDHYvm70OcWFuReQMtT3aeKNaQNgueJHWpLmFIQZz8zcAOglk1DtmQHzhGa0qDpAWFxy00TyMm3ZT9")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_84d697f22eda068596c45d3917ee7941a5970cad4d206dd237c85352117e1da7")
# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=QDRANT_URL,  # e.g. "http://localhost:6333" or your cloud URL,
    api_key=QDRANT_API_KEY
)

redis_client = Redis.from_url(REDIS_URL)
