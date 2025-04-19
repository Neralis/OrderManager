from ninja import Schema
from typing import Optional

class AuthIn(Schema):
    username: str
    password: str

class TokenOut(Schema):
    access: str
    refresh: str
