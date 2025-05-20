from django.contrib.auth import authenticate, login
from django.http import HttpRequest
from ninja import Router
from userApp.schemas import AuthIn, AuthOut

auth_router = Router(tags=["Аутентификация"])

@auth_router.post("/login", response=AuthOut)
def login_view(request: HttpRequest, data: AuthIn):
    user = authenticate(request, username=data.username, password=data.password)
    if user is not None:
        login(request, user)  # Сохраняет сессию
        return {"success": True, "message": "Login successful"}
    return {"success": False, "message": "Invalid credentials"}