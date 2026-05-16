from django.urls import path
from . import views

urlpatterns = [
    path('locker/', views.locker_wall, name='locker_wall'),
    path('locker/partial/', views.locker_wall_partial, name='locker_wall_partial'),
]
