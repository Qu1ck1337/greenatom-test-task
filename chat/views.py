from rest_framework import viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import User, Channel, Message
from chat.permissions import IsModerator, IsOwnerOrModerator, IsNotBlocked
from chat.serializers import UserSerializer, ChannelSerializer, MessageSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ChannelViewSet(viewsets.ModelViewSet):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrModerator]

    def perform_create(self, serializer):
        channel = serializer.save(owner=self.request.user)
        channel.members.add(self.request.user)


class ChannelJoinView(GenericAPIView):
    serializer_class = None
    permission_classes = [IsAuthenticated, IsNotBlocked]

    def post(self, request, channel_id):
        try:
            channel = Channel.objects.get(pk=channel_id)
            if request.user in channel.black_list.all():
                return Response(status=status.HTTP_403_FORBIDDEN)
            if request.user in channel.members.all():
                return Response({'status': 'already joined'})
            channel.members.add(request.user)
            channel.save()
            return Response(status=status.HTTP_200_OK)
        except Channel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ChannelLeaveView(APIView):
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def delete(self, request, channel_id):
        try:
            channel = Channel.objects.get(pk=channel_id)
            if request.user not in channel.members.all():
                return Response(status=status.HTTP_404_NOT_FOUND)
            channel.members.remove(request.user)
            channel.save()
            return Response(status=status.HTTP_200_OK)
        except Channel.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        channel_id = self.request.query_params.get('channel', None)
        return Message.objects.filter(channel_id=channel_id)

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


class BlockUserGloballyView(APIView):
    permission_classes = [IsAuthenticated, IsModerator]
    serializer_class = None

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            user.is_blocked = True
            user.save()
            return Response({'status': 'User has been blocked'})
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)