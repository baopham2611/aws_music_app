# ./backend/model/musics.py
from pydantic import BaseModel
from typing import Optional, List

class Music(BaseModel):
    music_id: str
    title: str
    artist: str
    year: int
    web_url: str
    img_url: str
    
    
class MusicResponse(BaseModel):
    musics: List[Music]
    total: int