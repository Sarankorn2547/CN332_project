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
from django.views.generic import RedirectView
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
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
    path('accounts/', include('allauth.urls')),
    path('kiosk/', include('kiosk.urls')),
    path('locker/', include('locker_wall.urls')),
    path('api/', include(router.urls)),
    path('api/users/status/', views.UserStatusView.as_view(), name='user-status'),
    path('api/users/register/', views.UserRegisterView.as_view(), name='user-register'),
    path('api/token/', views.LineUserTokenView.as_view(), name='token-obtain'),
    path('api/token/refresh/', views.LineUserTokenRefreshView.as_view(), name='token-refresh'),
    path('api/line/webhook/', views.LineWebhookView.as_view(), name='line-webhook'),
    path('api/line/push/', views.LinePushView.as_view(), name='line-push'),
    path('api/line/notify/', views.LineNotifyView.as_view(), name='line-notify'),
    path('api/system/reset/', views.SystemResetView.as_view(), name='system-reset'),
    path('api/admin/cli/', views.AdminCLIView.as_view(), name='admin-cli'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('', RedirectView.as_view(url='/kiosk/', permanent=False)),
]

from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
