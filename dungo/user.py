from fastapi import APIRouter, Depends
from config import redis_client
from datetime import datetime
from utils.auth import verify_token

users_router = APIRouter()


@users_router.get("/profile")
async def profile(user=Depends(verify_token)):
    now = datetime.utcnow()
    month_key = now.strftime("%Y-%m")

    # Create the Redis key
    redis_key = f"rate_limit:{user['id']}:{month_key}"
    used = await redis_client.get(redis_key)
    if used == None:
        used = 0
    user['used'] = int(used)
    return user
