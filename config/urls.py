"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from foodlocker import views

router = routers.DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'buildings', views.BuildingViewSet)
router.register(r'rooms', views.RoomViewSet)
router.register(r'lockers', views.LockerViewSet)
router.register(r'line-users', views.LineUserViewSet)
router.register(r'locker-logs', views.LockerLogViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/users/status/', views.UserStatusView.as_view(), name='user-status'),
    path('api/users/register/', views.UserRegisterView.as_view(), name='user-register'),
    path('api/token/', views.LineUserTokenView.as_view(), name='token-obtain'),
    path('api/token/refresh/', views.LineUserTokenRefreshView.as_view(), name='token-refresh'),
]