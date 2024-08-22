# ./frontend/application/model/musics.py

from flask_login import UserMixin
from werkzeug.security import check_password_hash

class Music(UserMixin):
    def __init__(self):
        pass