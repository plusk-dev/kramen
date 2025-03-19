from datetime import datetime
from fastapi import HTTPException, Header, Request
import jwt
from config import JWT_SECRET
from models import Integration, User, session
from utils.general import sqlalchemy_object_to_dict


def verify_token(token=Header(str, description="The user's JWT.")) -> bool:
    # token = request.headers.get("token")
    # if token is None:
    #     raise HTTPException(status_code=401, detail="JWT not provided")
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[
                                   "HS256"])  # Decode token
        # Check expiration
        if datetime.utcnow().timestamp() > decoded_token["exp"]:
            raise HTTPException(status_code=403, detail={
                                "message": "you are not logged in"})
        user_email = decoded_token['email']
        user = session.query(User).filter(User.email == user_email).first()
        if user is None:
            raise HTTPException(status_code=403, detail={
                                "message": "used with given email does not exist"})

        return sqlalchemy_object_to_dict(user)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        raise HTTPException(status_code=403, detail={
                            "message": "you are not logged in"})


def check_integration_ownership(integration_id, user_id):
    integration = session.query(Integration).filter(
        Integration.uuid == integration_id).first()
    if integration is None or integration.owner_id != user_id:
        return False
    return True
