from ninja import Schema
from pydantic import BaseModel, validator, field_validator


class AuthIn(Schema):
    username: str
    password: str

    @field_validator('username')
    def username_not_empty(cls, v):
        if not v.strip():
            raise ValueError("Username cannot be empty")
        return v


class AuthOut(Schema):
    success: bool
    message: str