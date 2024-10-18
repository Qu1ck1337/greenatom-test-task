from rest_framework import serializers

from chat.models import Channel, Message, User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'is_moderator', 'is_blocked']
        read_only_fields = ['is_moderator', 'is_blocked']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
        )
        return user


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ['id', 'name', 'owner', 'members', 'black_list']
        read_only_fields = ['members', 'owner']


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = Message
        fields = ['id', 'channel', 'sender', 'content', 'created_at']