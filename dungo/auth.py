import requests
import jwt
from fastapi import APIRouter, HTTPException
from config import JWT_EXPIRY_DAYS, JWT_SECRET
from schemas.dungo_schemas.auth import AuthenticationRequest
from models import User, session
from datetime import datetime, timedelta
from utils.general import sqlalchemy_object_to_dict
from utils.notifs.admin.discord import send_discord_message

# the prefix for this is /auth
auth_router = APIRouter()


async def verify_access_token(access_token: str):
    res = requests.get(
        "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token="+access_token)
    if res.status_code == 400:
        raise HTTPException(status_code=400, detail={
            "message": "your access token is invalid"
        })


@auth_router.post("")
async def auth(request: AuthenticationRequest):
    # verify_access_token(request.access_token)
    user = session.query(User).filter(User.email == request.email).first()
    sign_up = False
    if user is None:
        sign_up = True
        user = User(
            name=request.name,
            email=request.email,
            pfp=request.pfp,
            sign_up_method=request.sign_up_method,
            limit=0
        )
        session.add(user)
        session.commit()
        send_discord_message('signup', 'success', request.email + " just signed up !")
    response = sqlalchemy_object_to_dict(user)
    response['sign_up'] = sign_up

    return response


@auth_router.get("/token")
async def get_token(email: str):
    user = session.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=403, detail={
            "message": "user with given email does not exist"
        })

    data = sqlalchemy_object_to_dict(user)
    # Set expiration to 2 days
    expiration_time = datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS)
    data["exp"] = expiration_time  # Add expiration claim

    token = jwt.encode(payload=data, key=JWT_SECRET, algorithm='HS256')
    return {"token": token}
