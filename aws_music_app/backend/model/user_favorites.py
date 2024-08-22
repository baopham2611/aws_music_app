# ./backend/model/musics.py
from pydantic import BaseModel
from typing import Optional

class FavoriteRequest(BaseModel):
    user_email: str
    music_id: str