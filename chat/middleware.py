import jwt
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from chat_api import settings

@database_sync_to_async
def get_user(token):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import AnonymousUser

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.SIMPLE_JWT['ALGORITHM']])
        user = get_user_model().objects.get(id=payload['user_id'])
        return user
    except (jwt.DecodeError, get_user_model().DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser

        query_string = scope['query_string'].decode()
        token = None
        if 'token=' in query_string:
            token = query_string.split('token=', 1)[1]
        if token:
            scope['user'] = await get_user(token)
        else:
            scope['user'] = AnonymousUser()
        return await super().__call__(scope, receive, send)