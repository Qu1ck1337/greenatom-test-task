"""
ASGI config for chat_api project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from chat.middleware import JWTAuthMiddleware
from chat_api import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_api.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})
