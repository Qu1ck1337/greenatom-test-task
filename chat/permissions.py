from rest_framework import permissions


class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_moderator


class IsOwnerOrModerator(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "POST"]:
            return True
        return obj.owner == request.user or request.user.is_moderator


class IsNotBlocked(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_blocked