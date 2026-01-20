from django.contrib import admin
from .models import Category, MenuItem, CartItem, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'slug')

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'inventory', 'category', 'featured')
    list_filter = ('category', 'featured')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'menu_item', 'quantity', 'unit_price', 'created_at')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'delivery_crew', 'status', 'total', 'created_at')
    inlines = [OrderItemInline]
