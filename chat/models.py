from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_moderator = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)


class Channel(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='channels')

    def __str__(self):
        return self.name


class Message(models.Model):
    channel = models.ForeignKey(Channel, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.content[:20]}'