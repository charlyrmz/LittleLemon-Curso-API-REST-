from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Category, MenuItem, CartItem, Order, OrderItem
import bleach

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']

class MenuItemSerializer(serializers.ModelSerializer):
    # category as id by default
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'inventory', 'category', 'featured']

    def validate_title(self, value):
        # sanitize HTML/JS
        return bleach.clean(value)

    def validate(self, data):
        # ensure price >= 0 and inventory non-negative
        price = data.get('price', None)
        if price is not None and price < 0:
            raise serializers.ValidationError({'price': 'Price must be non-negative.'})
        inventory = data.get('inventory', None)
        if inventory is not None and inventory < 0:
            raise serializers.ValidationError({'inventory': 'Inventory must be non-negative.'})
        return data

class CartItemSerializer(serializers.ModelSerializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    class Meta:
        model = CartItem
        fields = ['id', 'menu_item', 'quantity', 'unit_price', 'created_at']
        read_only_fields = ['unit_price', 'created_at']

    def create(self, validated_data):
        user = self.context['request'].user
        menu_item = validated_data['menu_item']
        quantity = validated_data.get('quantity', 1)
        unit_price = menu_item.price
        obj, created = CartItem.objects.update_or_create(
            user=user, menu_item=menu_item,
            defaults={'quantity': quantity, 'unit_price': unit_price}
        )
        return obj

class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all())
    class Meta:
        model = OrderItem
        fields = ['id', 'menu_item', 'quantity', 'unit_price']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'created_at', 'order_items']
        read_only_fields = ['user', 'total', 'created_at', 'order_items']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['order_items'] = OrderItemSerializer(instance.order_items.all(), many=True).data
        return rep
