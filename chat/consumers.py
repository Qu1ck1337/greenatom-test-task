import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist, ValidationError

logger = logging.getLogger(__name__)

MESSAGE_TYPE_CHAT = 'chat_message'
MESSAGE_TYPE_WELCOME = 'welcome'
MESSAGE_TYPE_ERROR = 'error'

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs'].get('channel_id')
        if not self.channel_id:
            await self.close()
            return

        self.room_group_name = f'chat_{self.channel_id}'

        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        try:
            has_permission = await self.has_permission_to_channel(user, self.channel_id)
        except ObjectDoesNotExist:
            await self.close()
            return
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            await self.close()
            return

        if not has_permission:
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
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format.")
            return

        message_content = data.get('message')
        if not message_content:
            await self.send_error("Message content is missing.")
            return

        user = self.scope['user']

        try:
            has_permission = await self.has_permission_to_channel(user, self.channel_id)
        except ObjectDoesNotExist:
            await self.send_error("Channel does not exist.")
            return
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            await self.send_error("Internal server error.")
            return

        if not has_permission:
            await self.send_error("You do not have permission to send messages to this channel.")
            return

        try:
            message = await self.create_message(user, message_content)
            serialized_message = await self.serialize_message(message)
        except ValidationError as ve:
            await self.send_error(f"Validation error: {ve}")
            return
        except Exception as e:
            logger.error(f"Error creating message: {e}")
            await self.send_error("Failed to create message.")
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': MESSAGE_TYPE_CHAT,
                'message': serialized_message
            }
        )

    async def chat_message(self, event):
        message = event.get('message')
        if message:
            await self.send(text_data=json.dumps(message))

    async def send_welcome_message(self):
        try:
            recent_messages = await self.get_recent_messages()
            serialized_messages = await self.serialize_messages(recent_messages)

            welcome_data = {
                'type': MESSAGE_TYPE_WELCOME,
                'message': 'Welcome to the chat!',
                'user': self.scope['user'].username,
                'history': serialized_messages
            }
            await self.send(text_data=json.dumps(welcome_data))
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            error_data = {
                'type': MESSAGE_TYPE_ERROR,
                'message': "Couldn't load message history."
            }
            await self.send(text_data=json.dumps(error_data))

    async def send_error(self, error_message):
        error_data = {
            'type': MESSAGE_TYPE_ERROR,
            'message': error_message
        }
        await self.send(text_data=json.dumps(error_data))

    async def force_disconnect(self, event):
        target_user_id = event['user_id']

        if self.scope['user'].id == target_user_id:
            await self.close(code=4000, reason='You were deleted from chat')

    @database_sync_to_async
    def get_recent_messages(self, limit=20):
        from chat.models import Message
        return Message.objects.filter(channel_id=self.channel_id).select_related('sender').order_by('-created_at')[:limit]

    @database_sync_to_async
    def serialize_messages(self, messages):
        from chat.serializers import MessageSerializer
        return MessageSerializer(messages, many=True).data

    @database_sync_to_async
    def serialize_message(self, message):
        from chat.serializers import MessageSerializer
        return MessageSerializer(message).data

    @database_sync_to_async
    def create_message(self, user, content):
        from chat.models import Message, Channel
        channel = Channel.objects.prefetch_related('members').get(id=self.channel_id)
        if user.is_blocked:
            raise ValidationError("User is blocked.")
        return Message.objects.create(channel=channel, sender=user, content=content)

    @database_sync_to_async
    def has_permission_to_channel(self, user, channel_id) -> bool:
        from chat.models import Channel
        try:
            channel = Channel.objects.prefetch_related('members').get(id=channel_id)
            return user.is_moderator or (user in channel.members.all() and not user.is_blocked)
        except Channel.DoesNotExist:
            return False