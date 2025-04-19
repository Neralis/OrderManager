import secrets

from django.contrib.auth import authenticate
from ninja import Router
from rest_framework_simplejwt.tokens import RefreshToken

from userApp.schemas import AuthIn, TokenOut

auth_router = Router(tags=["Аутентификация"])

@auth_router.post("/login", response={200: TokenOut, 401: dict}, auth=None)
def login(request, data: AuthIn):
    user = authenticate(username=data.username, password=data.password)
    if user:
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }
    return 401, {"detail": "Неверный логин или пароль"}