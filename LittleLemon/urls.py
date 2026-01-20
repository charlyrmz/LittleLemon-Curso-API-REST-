from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('LittleLemonAPI.urls')),
    # Djoser endpoints for user registration and token login
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),  # if using token auth
    # if using JWT:
    # path('api/auth/', include('djoser.urls.jwt')),
]
