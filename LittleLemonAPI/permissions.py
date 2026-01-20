from rest_framework import permissions

def user_in_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and user_in_group(request.user, 'Manager')

class IsDeliveryCrew(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and user_in_group(request.user, 'Delivery crew')

class IsManagerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated and user_in_group(request.user, 'Manager')

class IsOwnerOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # allow manager full access, owner limited
        if request.user and request.user.is_authenticated and user_in_group(request.user, 'Manager'):
            return True
        return obj.user == request.user
