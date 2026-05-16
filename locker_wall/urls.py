from django.urls import path
from . import views
from .views_dashboard import dashboard

urlpatterns = [
    path('', views.locker_wall, name='locker_wall'),
    path('partial/', views.locker_wall_partial, name='locker_wall_partial'),
    path('test-door/', views.test_door, name='test_door'),
    path('dashboard/', dashboard, name='dashboard'),
]
