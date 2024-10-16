from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import User, Channel, Message
from chat.permissions import IsModerator
from chat.serializers import UserSerializer, ChannelSerializer, MessageSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        channel_id = self.request.query_params.get('channel', None)
        return Message.objects.filter(channel_id=channel_id)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class BlockUserView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]
    serializer_class = None

    def post(self, request, pk=None, format=None):
        try:
            user = User.objects.get(pk=pk)
            user.is_moderator = True
            user.save()
            return Response({'status': 'User has been blocked'})
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)