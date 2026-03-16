from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, Building, Room, Locker, LineUser, LockerLog
from .serializers import (
    ProjectSerializer,
    BuildingSerializer,
    RoomSerializer,
    LockerSerializer,
    LineUserSerializer,
    LockerLogSerializer,
)
from .services import LockerService

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class BuildingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BuildingSerializer

    def get_queryset(self):
        queryset = Building.objects.all()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoomSerializer

    def get_queryset(self):
        queryset = Room.objects.all()
        building_id = self.request.query_params.get('building_id')
        if building_id:
            queryset = queryset.filter(building_id=building_id)
        return queryset

class LockerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Locker.objects.all()
    serializer_class = LockerSerializer

    @action(detail=False, methods=['post'])
    def book(self, request):
        building_id = request.data.get('building_id')
        size = request.data.get('size')
        locker_type = request.data.get('type')

        if not all([building_id, size, locker_type]):
            return Response({'error': 'building_id, size, and type are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            locker = LockerService.book_locker(building_id, size, locker_type)
            return Response({
                'locker_id': locker.id,
                'qr_data': locker.qr_data,
                'passcode': locker.passcode
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def open(self, request, pk=None):
        try:
            locker = LockerService.open_locker(locker_id=pk)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        try:
            locker = LockerService.confirm_deposit(locker_id=pk)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='verify-qr')
    def verify_qr(self, request):
        qr_data = request.data.get('qr_data')
        passcode = request.data.get('passcode')
        
        try:
            locker = LockerService.verify_qr(qr_data=qr_data, passcode=passcode)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def pickup(self, request, pk=None):
        try:
            locker = LockerService.pickup_locker(locker_id=pk)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LineUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LineUser.objects.all()
    serializer_class = LineUserSerializer

class LockerLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LockerLog.objects.all()
    serializer_class = LockerLogSerializer