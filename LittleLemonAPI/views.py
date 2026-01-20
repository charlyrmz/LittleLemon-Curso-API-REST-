from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework import generics, status, viewsets, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend

from .models import Category, MenuItem, CartItem, Order, OrderItem
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    CartItemSerializer,
    OrderSerializer,
    OrderItemSerializer,
)
from .permissions import IsManager, IsDeliveryCrew, IsManagerOrReadOnly, IsOwnerOrManager

User = get_user_model()

# Pagination
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50


# Categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


# Menu items
class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsManagerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title']
    ordering_fields = ['price', 'title', 'id']
    filterset_fields = ['category', 'featured']

    def get_permissions(self):
        # GET allowed for customers/delivery crew; POST/PUT/PATCH/DELETE only for Manager
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsManager()]
        return [AllowAny()]


# Group management endpoints (Manager only)
class ManagerGroupUsersView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        managers = User.objects.filter(groups__name='Manager')
        data = [{'id': u.id, 'username': u.username, 'email': u.email} for u in managers]
        return Response(data)

    def post(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        group, _ = Group.objects.get_or_create(name='Manager')
        user.groups.add(group)
        return Response({'message': 'user added to the manager group'}, status=status.HTTP_201_CREATED)


class ManagerGroupUserDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.filter(name='Manager').first()
        if not group or not user.groups.filter(name='Manager').exists():
            return Response({'detail': 'User not in manager group'}, status=status.HTTP_404_NOT_FOUND)
        user.groups.remove(group)
        return Response({'message': 'user removed from manager group'}, status=status.HTTP_200_OK)


class DeliveryGroupUsersView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        users = User.objects.filter(groups__name='Delivery crew')
        data = [{'id': u.id, 'username': u.username, 'email': u.email} for u in users]
        return Response(data)

    def post(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        group, _ = Group.objects.get_or_create(name='Delivery crew')
        user.groups.add(group)
        return Response({'message': 'user added to delivery crew group'}, status=status.HTTP_201_CREATED)


class DeliveryGroupUserDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.filter(name='Delivery crew').first()
        if not group or not user.groups.filter(name='Delivery crew').exists():
            return Response({'detail': 'User not in delivery crew group'}, status=status.HTTP_404_NOT_FOUND)
        user.groups.remove(group)
        return Response({'message': 'user removed from delivery crew group'}, status=status.HTTP_200_OK)


# Cart endpoints
class CartMenuItemsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()
        data['unit_price'] = 0  # will be set in serializer create
        serializer = CartItemSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response({'message': 'cart cleared'}, status=status.HTTP_200_OK)


# Orders
class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter]
    ordering_fields = ['created_at', 'total', 'status']
    filterset_fields = ['status', 'delivery_crew']
    search_fields = ['user__username']

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name='Manager').exists():
            return Order.objects.all().order_by('-created_at')
        if user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=user).order_by('-created_at')
        # customer
        return Order.objects.filter(user=user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)
        if not cart_items.exists():
            return Response({'detail': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            order = Order.objects.create(user=user)
            total = 0
            for ci in cart_items:
                OrderItem.objects.create(
                    order=order,
                    menu_item=ci.menu_item,
                    quantity=ci.quantity,
                    unit_price=ci.unit_price
                )
                total += ci.quantity * ci.unit_price
            order.total = total
            order.save()
            cart_items.delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        # Delivery crew can update status only; Manager can set delivery_crew and status
        order = self.get_object()
        user = request.user
        data = request.data
        if user.groups.filter(name='Delivery crew').exists():
            # only allow status update
            status_val = data.get('status', None)
            if status_val is None:
                return Response({'detail': 'status required'}, status=status.HTTP_400_BAD_REQUEST)
            order.status = status_val
            order.save()
            return Response(OrderSerializer(order).data)
        if user.groups.filter(name='Manager').exists():
            # allow updating delivery_crew and status
            delivery_id = data.get('delivery_crew', None)
            if delivery_id:
                delivery_user = get_object_or_404(User, id=delivery_id)
                order.delivery_crew = delivery_user
            if 'status' in data:
                order.status = data.get('status')
            order.save()
            return Response(OrderSerializer(order).data)
        return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)
