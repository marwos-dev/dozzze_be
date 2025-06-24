from ninja import Router
from ninja.security import HttpBearer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from pydantic import BaseModel, EmailStr
from typing import Optional
from django.contrib.auth import authenticate
from django.http import HttpRequest
from ninja.errors import HttpError

class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        from rest_framework_simplejwt.authentication import JWTAuthentication

        jwt_authenticator = JWTAuthentication()
        validated_token = jwt_authenticator.get_validated_token(token)
        user = jwt_authenticator.get_user(validated_token)
        request.user = user
        return token