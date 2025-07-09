from typing import Optional

from ninja import Schema
from pydantic import EmailStr


class SignUpIn(Schema):
    email: EmailStr
    password: str


class TokenOut(Schema):
    access: str
    refresh: str
    email: EmailStr | None
    first_name: str

class LoginIn(Schema):
    email: EmailStr
    password: str


class ProfileOut(Schema):
    email: str


class ProfileUpdateIn(Schema):
    email: Optional[EmailStr] = None


class RefreshTokenIn(Schema):
    refresh: str
