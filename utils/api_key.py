import hashlib
from models import APIKey, session


def validate_api_key(key: str):
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    api_key = session.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    if api_key is None:
        return False
    rate_limit(key_hash=key_hash)


def rate_limit(key_hash: str):
    return True
