from django.urls import path
from . import views

urlpatterns = [
    path('locker/', views.locker_wall, name='locker_wall'),
    path('locker/partial/', views.locker_wall_partial, name='locker_wall_partial'),
    path('locker/test-door/', views.test_door, name='test_door'),
]
