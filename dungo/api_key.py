import hashlib
import secrets
from models import APIKey, session
from fastapi import APIRouter, Depends, HTTPException

from schemas.dungo_schemas.api_key import CreateAPIKeyModel, DeleteAPIKeyModel
from utils.auth import verify_token
from utils.general import sqlalchemy_object_to_dict

api_key_router = APIRouter()


@api_key_router.get("/all")
async def get_all_keys(user=Depends(verify_token)):
    keys = session.query(APIKey).filter(APIKey.user_id == user['id']).all()
    res = []
    for k in keys:
        res.append(sqlalchemy_object_to_dict(k))

    return res


@api_key_router.post("/create")
async def create_api_key(request: CreateAPIKeyModel, user=Depends(verify_token)):
    apikey = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(apikey.encode()).hexdigest()

    key = APIKey(
        user_id=user['id'],
        key_hash=key_hash,
        name=request.name
    )
    session.add(key)
    session.commit()

    data = sqlalchemy_object_to_dict(key)
    data['real'] = apikey

    return data


@api_key_router.post("/delete")
async def delete_api_key(request: DeleteAPIKeyModel, user=Depends(verify_token)):
    key = session.query(APIKey).filter(
        APIKey.id == request.id,
        APIKey.user_id == user["id"]
    ).first()

    if key is None:
        raise HTTPException(status_code=404, detail={
                            "message": "API key not found"})

    session.delete(key)
    session.commit()

    return {"message": "API key deleted successfully"}
