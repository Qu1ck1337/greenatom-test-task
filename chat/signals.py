from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from chat.models import Channel


@receiver(m2m_changed, sender=Channel.members.through)
def notify_user_removal(sender, instance, action, pk_set, **kwargs):
    if action == "pre_remove":
        user_ids = pk_set
        channel_id = instance.id

        channel_layer = get_channel_layer()
        group_name = f'chat_{channel_id}'

        for user_id in user_ids:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    'type': 'force_disconnect',
                    'user_id': user_id,
                }
            )


#todo make with "is_blocked" state