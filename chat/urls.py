from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.views import (UserViewSet, MessageViewSet, ChannelViewSet, ChannelJoinView, ChannelLeaveView,
                        BlockUserGloballyView)

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'channels', ChannelViewSet)
router.register(r'messages', MessageViewSet, basename='messages')

urlpatterns = [
    path('', include(router.urls)),
    path('moderator/block-globally/<int:user_id>/', BlockUserGloballyView.as_view(), name='block-user'),
    path('channels/join/<int:channel_id>/', ChannelJoinView.as_view(), name='channels'),
    path('channels/leave/<int:channel_id>/', ChannelLeaveView.as_view(), name='channels'),
]