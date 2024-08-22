# ./backend/model/users.py
from pydantic import BaseModel
from typing import Optional

class UserResponse(BaseModel):
    email: str
    user_name: str
    # Do not include password here for security

class User(BaseModel):
    email: str
    user_name: str
    password: str  # This can remain for internal use where needed

class UpdateUser(BaseModel):
    user_name: Optional[str] = None
    password: Optional[str] = None

class LoginCredentials(BaseModel):
    email: str
    password: str
