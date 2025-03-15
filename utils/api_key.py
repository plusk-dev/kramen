import hashlib
from datetime import datetime, timedelta

from fastapi import HTTPException
from config import redis_client
from models import APIKey, User, session

async def validate_api_key(key: str):
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    api_key = session.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    if api_key is None:
        return False
    return await rate_limit(api_key.user)

async def rate_limit(user: User):
    print("rate limiting a user")
    user_id = user.id
    user_limit = user.limit  # Monthly request limit

    # Get the current month and year to create a unique key for each month
    now = datetime.utcnow()
    month_key = now.strftime("%Y-%m")

    # Create the Redis key
    redis_key = f"rate_limit:{user_id}:{month_key}"

    # Increment the request count for this user in the current month
    current_count = await redis_client.incr(redis_key)

    # If this is the first request in the month, set an expiration time for the key
    if current_count == 1:
        # Set the key to expire at the end of the month
        next_month = (now.replace(day=1) + timedelta(days=32)).replace(day=1)
        expire_at = next_month - now
        await redis_client.expire(redis_key, int(expire_at.total_seconds()))

    # Check if the user has exceeded their monthly limit
    if current_count > user_limit:
        raise HTTPException(status_code=429, detail={
            "message": "your rate limit of " + str(user_limit) + " requests per month has been exhausted for this month. upgrade your limit at https://kramen.tech/landing/pricing or try again next month."
        })