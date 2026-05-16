from django.urls import path
from . import views
from .views_dashboard import dashboard
from .views_cli import cli_view

urlpatterns = [
    path('', views.locker_wall, name='locker_wall'),
    path('partial/', views.locker_wall_partial, name='locker_wall_partial'),
    path('test-door/', views.test_door, name='test_door'),
    path('dashboard/', dashboard, name='dashboard'),
    path('cli/', cli_view, name='cli'),
]
