from functools import wraps
from django.http import HttpRequest
from ninja.errors import HttpError


def group_required(*group_names):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.user.is_authenticated:
                raise HttpError(401, "Unauthorized")
            if not request.user.groups.filter(name__in=group_names).exists():
                raise HttpError(403, f"Requires groups: {', '.join(group_names)}")
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator