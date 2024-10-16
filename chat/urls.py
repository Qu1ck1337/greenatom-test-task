from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat.views import UserViewSet, MessageViewSet, ChannelViewSet, BlockUserView

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'channels', ChannelViewSet)
router.register(r'messages', MessageViewSet, basename='messages')
# router.register(r'moderator', ModeratorViewSet, basename='moderator')

urlpatterns = [
    path('', include(router.urls)),
    path('moderator/block/<int:pk>/', BlockUserView.as_view(), name='block-user'),
]