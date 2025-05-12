from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: Optional[int] = None
    username: str
    email: EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


