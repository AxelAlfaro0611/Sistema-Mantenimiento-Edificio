from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

class LoginRequiredMiddleware:
    """
    Redirige a login si el usuario no está autenticado
    (excepto para las URLs permitidas como login, logout, admin, static, media).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_urls = [
            reverse('login'),
            reverse('logout'),
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not any(request.path.startswith(path) for path in self.allowed_urls + ['/static/', '/media/', '/admin/']):
                return redirect('login')
        return self.get_response(request)
