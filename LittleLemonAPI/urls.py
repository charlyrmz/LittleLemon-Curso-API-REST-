from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuItemViewSet, CategoryListView,
    ManagerGroupUsersView, ManagerGroupUserDeleteView,
    DeliveryGroupUsersView, DeliveryGroupUserDeleteView,
    CartMenuItemsView, OrdersViewSet
)

router = DefaultRouter()
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'orders', OrdersViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('categories/', CategoryListView.as_view(), name='categories'),
    # groups
    path('groups/manager/users', ManagerGroupUsersView.as_view(), name='manager-users'),
    path('groups/manager/users/<int:user_id>', ManagerGroupUserDeleteView.as_view(), name='manager-user-delete'),
    path('groups/delivery-crew/users', DeliveryGroupUsersView.as_view(), name='delivery-users'),
    path('groups/delivery-crew/users/<int:user_id>', DeliveryGroupUserDeleteView.as_view(), name='delivery-user-delete'),
    # cart
    path('cart/menu-items', CartMenuItemsView.as_view(), name='cart-menu-items'),
]
