from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.views import (MessageViewSet, ChannelViewSet, ChannelJoinView, ChannelLeaveView,
                        BlockUserGloballyView, RegisterView)

router = DefaultRouter()
router.register(r'channels', ChannelViewSet)
router.register(r'messages', MessageViewSet, basename='messages')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='user-register'),
    path('moderator/block-globally/<int:user_id>/', BlockUserGloballyView.as_view(), name='block-user'),
    path('channels/join/<int:pk>/', ChannelJoinView.as_view(), name='channel-join'),
    path('channels/leave/<int:pk>/', ChannelLeaveView.as_view(), name='channel-leave'),
]