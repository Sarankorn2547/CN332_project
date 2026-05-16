import shlex

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from .models import Project, Building, Room, Locker, LineUser, LockerLog
from .serializers import (
    ProjectSerializer,
    BuildingSerializer,
    RoomSerializer,
    LockerSerializer,
    LockerUpdateSerializer,
    LineUserSerializer,
    LockerLogSerializer,
)
from .line_service import LineService
from .authentication import LineUserJWTAuthentication
from .services import LockerService


class LineUserTokenView(APIView):
    def post(self, request):
        line_user_id = request.data.get('line_user_id')
        if not line_user_id:
            return Response({'error': 'line_user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            line_user = LineUser.objects.get(line_user_id=line_user_id)
        except LineUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        refresh = RefreshToken()
        refresh['line_user_id'] = line_user.line_user_id
        refresh['display_name'] = line_user.display_name
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class _LineUserTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])
        return {'access': str(refresh.access_token)}


class LineUserTokenRefreshView(BaseTokenRefreshView):
    serializer_class = _LineUserTokenRefreshSerializer


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

class LockerViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Locker.objects.all()
    serializer_class = LockerSerializer

    def get_queryset(self):
        qs = Locker.objects.all()
        building_id = self.request.query_params.get('building_id')
        if building_id:
            qs = qs.filter(building_id=building_id)
        return qs

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return LockerUpdateSerializer
        return LockerSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def open(self, request, pk=None):
        try:
            locker = LockerService.open_locker(locker_id=pk)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def deposit(self, request, pk=None):
        try:
            locker = LockerService.confirm_deposit(locker_id=pk)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='verify-qr', permission_classes=[IsAuthenticated])
    def verify_qr(self, request):
        qr_data = request.data.get('qr_data')
        passcode = request.data.get('passcode')
        
        try:
            locker = LockerService.verify_qr(qr_data=qr_data, passcode=passcode)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='pickup', permission_classes=[IsAuthenticated])
    def pickup(self, request, pk=None):
        actor_id = request.data.get('actor_id', 'customer')
        try:
            locker = LockerService.pickup_locker(locker_id=pk, actor_id=actor_id)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LineWebhookView(APIView):
    def post(self, request):
        signature = request.headers.get('X-Line-Signature', '')
        body = request.body

        if not LineService.verify_signature(body, signature):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)

        events = request.data.get('events', [])
        for event in events:
            # Event handling can be extended here per event type
            pass

        return Response({'status': 'ok'}, status=status.HTTP_200_OK)


class LinePushView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        to = request.data.get('to')
        text = request.data.get('message')
        image_url = request.data.get('image_url')

        if not to:
            return Response({'error': 'to is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not text and not image_url:
            return Response(
                {'error': 'message or image_url is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if text and image_url:
                result = LineService.push_text_and_image(to, text, image_url)
            elif text:
                result = LineService.push_text(to, text)
            else:
                result = LineService.push_image(to, image_url)
            return Response({'status': 'ok', 'result': result}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LineUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LineUser.objects.all()
    serializer_class = LineUserSerializer

class LockerLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LockerLog.objects.all()
    serializer_class = LockerLogSerializer


class SystemResetView(APIView):
    """Reset lockers to AVAILABLE state. Scope: LOCKER | BUILDING | PROJECT | ALL."""

    authentication_classes = [LineUserJWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        actor_id = getattr(request.user, 'line_user_id', None) or getattr(request.user, 'username', 'system')

        try:
            result = LockerService.reset_lockers(
                request.data.get('scope'),
                locker_id=request.data.get('locker_id'),
                building_id=request.data.get('building_id'),
                project_id=request.data.get('project_id'),
                actor_id=actor_id,
            )
        except Locker.DoesNotExist as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'message': f"{result['reset_count']} locker(s) reset successfully",
            **result,
        }, status=status.HTTP_200_OK)


class AdminCLIView(APIView):
    """Execute admin CLI commands: list, open <id>, reset <scope>."""

    authentication_classes = [LineUserJWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        command = request.data.get('command')
        if not isinstance(command, str) or not command.strip():
            return Response(
                {'error': 'command is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tokens = shlex.split(command)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        action = tokens[0].lower()
        args = tokens[1:]
        actor_id = getattr(request.user, 'line_user_id', None) or getattr(request.user, 'username', 'system')

        try:
            if action == 'list':
                return self._list(args)
            if action == 'open':
                return self._open(args, actor_id)
            if action == 'reset':
                return self._reset(args, actor_id)
        except Locker.DoesNotExist as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'error': f"Unknown command '{action}'. Supported commands: list, open, reset."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def _list(self, args):
        filters = self._parse_options(args, allowed={'--building', '--status', '--type'})
        queryset = Locker.objects.all().order_by('building_id', 'local_id', 'id')

        building_id = filters.get('--building')
        if building_id:
            queryset = queryset.filter(building_id=building_id)

        locker_status = filters.get('--status')
        if locker_status:
            queryset = queryset.filter(status=locker_status.upper())

        locker_type = filters.get('--type')
        if locker_type:
            queryset = queryset.filter(type=locker_type.upper())

        return Response({
            'command': 'list',
            'count': queryset.count(),
            'lockers': LockerSerializer(queryset, many=True).data,
        }, status=status.HTTP_200_OK)

    def _open(self, args, actor_id):
        if len(args) != 1:
            raise ValueError('Usage: open <locker_id>')

        locker = LockerService.open_locker(args[0], actor_id=actor_id)
        return Response({
            'command': 'open',
            'message': f"Locker {locker.id} opened successfully",
            'locker': LockerSerializer(locker).data,
        }, status=status.HTTP_200_OK)

    def _reset(self, args, actor_id):
        if not args:
            raise ValueError('Usage: reset <locker_id> | reset --building=<id> | reset --project=<id> | reset --all')
        if len(args) != 1:
            raise ValueError('Usage: reset <locker_id> | reset --building=<id> | reset --project=<id> | reset --all')

        if args[0] == '--all':
            result = LockerService.reset_lockers('ALL', actor_id=actor_id)
        elif args[0].startswith('--building='):
            result = LockerService.reset_lockers(
                'BUILDING',
                building_id=args[0].split('=', 1)[1],
                actor_id=actor_id,
            )
        elif args[0].startswith('--project='):
            result = LockerService.reset_lockers(
                'PROJECT',
                project_id=args[0].split('=', 1)[1],
                actor_id=actor_id,
            )
        elif args[0].startswith('--'):
            raise ValueError('Usage: reset <locker_id> | reset --building=<id> | reset --project=<id> | reset --all')
        else:
            result = LockerService.reset_lockers('LOCKER', locker_id=args[0], actor_id=actor_id)

        return Response({
            'command': 'reset',
            'message': f"{result['reset_count']} locker(s) reset successfully",
            **result,
        }, status=status.HTTP_200_OK)

    def _parse_options(self, args, allowed):
        filters = {}
        for arg in args:
            if '=' not in arg:
                raise ValueError(f"Invalid option '{arg}'. Use --name=value format.")
            key, value = arg.split('=', 1)
            if key not in allowed:
                raise ValueError(f"Unsupported option '{key}'.")
            filters[key] = value
        return filters
