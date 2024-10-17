import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group_name = f'chat_{self.channel_id}'

        if (not self.scope['user'].is_authenticated or
                not await self.has_permission_to_channel(self.scope['user'], self.channel_id)):
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_welcome_message()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_content = data['message']
        user = self.scope['user']

        channel = await self.get_channel(self.channel_id)
        message = await self.create_message(channel, user, message_content)

        from chat.serializers import MessageSerializer
        serializer = MessageSerializer(message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': serializer.data
            }
        )

    async def chat_message(self, event):
        message = event['message']

        await self.send(text_data=json.dumps(message))

    async def send_welcome_message(self):
        try:
            recent_messages = await self.get_recent_messages()

            serialized_messages = await self.serialize_messages(recent_messages)

            welcome_data = {
                'type': 'welcome',
                'message': 'Welcome to the chat!',
                'user': self.scope['user'].username if self.scope['user'].is_authenticated else 'Anonym',
                'history': serialized_messages
            }
            await self.send(text_data=json.dumps(welcome_data))
        except Exception as e:
            error_data = {
                'type': 'error',
                'message': "Couldn't load message history",
                'details': str(e)
            }
            await self.send(text_data=json.dumps(error_data))

    @database_sync_to_async
    def get_recent_messages(self, limit=20):
        from chat.models import Message
        return Message.objects.filter(channel_id=self.channel_id).order_by('-created_at')[:limit]

    @database_sync_to_async
    def serialize_messages(self, messages):
        from chat.serializers import MessageSerializer
        return MessageSerializer(messages, many=True).data

    @database_sync_to_async
    def get_channel(self, channel_id):
        from chat.models import Channel
        return Channel.objects.get(id=channel_id)

    @database_sync_to_async
    def create_message(self, channel, user, content):
        from chat.models import Message
        return Message.objects.create(channel=channel, sender=user, content=content)

    @database_sync_to_async
    def has_permission_to_channel(self, user, channel_id) -> bool:
        from chat.models import Channel
        return user in Channel.objects.get(id=channel_id).members.all()