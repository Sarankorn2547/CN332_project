from django.urls import re_path

from .consumers import LockerConsumer

websocket_urlpatterns = [
    re_path(r"^ws/lockers/(?P<building_id>[^/]+)/$", LockerConsumer.as_asgi()),
]
