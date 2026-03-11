from rest_framework import viewsets
from .models import Project, Building, Room, Locker, LineUser, LockerLog
from .serializers import (
    ProjectSerializer,
    BuildingSerializer,
    RoomSerializer,
    LockerSerializer,
    LineUserSerializer,
    LockerLogSerializer,
)

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class BuildingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class LockerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Locker.objects.all()
    serializer_class = LockerSerializer

class LineUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LineUser.objects.all()
    serializer_class = LineUserSerializer

class LockerLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LockerLog.objects.all()
    serializer_class = LockerLogSerializer