from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, HttpResponse
from ninja import Router
from userApp.schemas import AuthIn, AuthOut
from django.middleware.csrf import get_token

auth_router = Router(tags=["Аутентификация"])

@auth_router.post("/login", response=AuthOut)
def login_view(request: HttpRequest, data: AuthIn):
    user = authenticate(request, username=data.username, password=data.password)
    if user is not None:
        login(request, user)  # Сохраняет сессию
        return {"success": True, "message": "Login successful"}
    return {"success": False, "message": "Invalid credentials"}

@auth_router.post("/logout")
def logout_user(request: HttpRequest):
    logout(request)
    return {"message": "Вы вышли из аккаунта"}

@auth_router.get("/user")
def get_user_info(request: HttpRequest):
    if request.user.is_authenticated:
        return {
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "groups": [group.name for group in request.user.groups.all()],
            "is_authenticated": True
        }
    return {"is_authenticated": False}

@auth_router.get("/csrf")
def get_csrf_token(request: HttpRequest):
    token = get_token(request)
    response = HttpResponse()
    response["X-CSRFToken"] = token
    return response