from pydantic import BaseModel

class AuthenticationRequest(BaseModel):
    name: str
    email: str
    pfp: str
    sign_up_method: str
