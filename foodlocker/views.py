from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
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

class UserRegisterView(APIView):
    def post(self, request):
        # Extract required fields from request
        line_user_id = request.data.get('line_user_id')
        project_id = request.data.get('project_id')
        building_id = request.data.get('building_id')
        room_no = request.data.get('room_no')
        display_name = request.data.get('display_name')

        # Validate all required fields are present
        if not all([line_user_id, project_id, building_id, room_no, display_name]):
            return Response(
                {'error': 'line_user_id, project_id, building_id, room_no, and display_name are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user already exists
        if LineUser.objects.filter(line_user_id=line_user_id).exists():
            return Response(
                {'error': 'User with this line_user_id already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if project and building exist
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            building = Building.objects.get(id=building_id, project=project)
        except Building.DoesNotExist:
            return Response({'error': 'Building not found'}, status=status.HTTP_404_NOT_FOUND)

        # Create the new LineUser
        try:
            line_user = LineUser.objects.create(
                line_user_id=line_user_id,
                project=project,
                building=building,
                room_no=room_no,
                display_name=display_name
            )
            serializer = LineUserSerializer(line_user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserStatusView(APIView):
    def get(self, request):
        line_user_id = request.query_params.get('line_user_id')
        if not line_user_id:
            return Response({'error': 'line_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user exists
        try:
            LineUser.objects.get(line_user_id=line_user_id)
        except LineUser.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Find lockers associated with the user that are not 'AVAILABLE'
        locker_ids = LockerLog.objects.filter(actor_id=line_user_id).values_list('locker_id', flat=True).distinct()
        active_lockers = Locker.objects.filter(id__in=locker_ids).exclude(status="AVAILABLE")

        if not active_lockers.exists():
            return Response({
                "status": "NO_ACTIVE_LOCKER",
                "lockers": []
            }, status=status.HTTP_200_OK)


        serializer = LockerSerializer(active_lockers, many=True)
        return Response({
            "status": "HAS_ACTIVE_LOCKER",
            "lockers": serializer.data
        }, status=status.HTTP_200_OK)

class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class BuildingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer

    def get_queryset(self):
        queryset = Building.objects.all()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Room.objects.all()
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