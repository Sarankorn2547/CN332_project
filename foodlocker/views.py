import shlex

from rest_framework import viewsets, mixins, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
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
from .realtime import broadcast_locker_update


def _request_actor_id(request, default='system'):
    return (
        getattr(request.user, 'line_user_id', None)
        or getattr(request.user, 'username', None)
        or request.data.get('actor_id')
        or default
    )


def _actor_id(request, fallback='system'):
    return (
        getattr(request.user, 'line_user_id', None)
        or getattr(request.user, 'username', None)
        or fallback
    )


class IsAuthenticatedOrKiosk(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        referer = request.META.get('HTTP_REFERER', '')
        if '/kiosk/' in referer:
            return True
        if request.session and request.session.get('_auth_user_id'):
            return True
        return False


class LineUserTokenView(APIView):
    @extend_schema(
        summary="Obtain JWT token pair",
        description="Issue an access + refresh JWT pair for a registered LINE user.",
        request={"application/json": {"type": "object", "properties": {"line_user_id": {"type": "string"}}, "required": ["line_user_id"]}},
        responses={
            200: OpenApiResponse(description="Returns access and refresh tokens."),
            400: OpenApiResponse(description="line_user_id is missing."),
            404: OpenApiResponse(description="User not found."),
        },
        auth=[],
    )
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
    @extend_schema(
        summary="Register a LINE user",
        description="Create a new LineUser linking a LINE user ID to a project, building, and room.",
        request={"application/json": {"type": "object", "properties": {
            "line_user_id": {"type": "string"},
            "project_id": {"type": "string"},
            "building_id": {"type": "string"},
            "room_no": {"type": "string"},
            "display_name": {"type": "string"},
        }, "required": ["line_user_id", "project_id", "building_id", "room_no", "display_name"]}},
        responses={
            201: LineUserSerializer,
            400: OpenApiResponse(description="Missing fields or duplicate line_user_id."),
            404: OpenApiResponse(description="Project or Building not found."),
        },
        auth=[],
    )
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

        # Check if project and building exist
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            building = Building.objects.get(id=building_id, project=project)
        except Building.DoesNotExist:
            return Response({'error': 'Building not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the room/building is already registered to a DIFFERENT user
        other_user_taken = LineUser.objects.filter(
            building_id=building_id, 
            room_no=room_no
        ).exclude(line_user_id=line_user_id).exists()
        
        if other_user_taken:
            return Response(
                {'error': f'ห้อง {room_no} ของอาคารนี้มีลูกบ้านท่านอื่นลงทะเบียนไว้แล้ว'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create or Update the LineUser
        created = False
        try:
            existing_user = LineUser.objects.filter(line_user_id=line_user_id).first()
            if existing_user:
                existing_user.project = project
                existing_user.building = building
                existing_user.room_no = room_no
                existing_user.display_name = display_name
                existing_user.save()
                line_user = existing_user
            else:
                line_user = LineUser.objects.create(
                    line_user_id=line_user_id,
                    project=project,
                    building=building,
                    room_no=room_no,
                    display_name=display_name
                )
                created = True

            # Send LINE confirmation push notification
            confirm_message = (
                f"✅ Registration Confirmed!\n\n"
                f"Project: {project.name}\n"
                f"Building: {building.name}\n"
                f"Room: {room_no}\n\n"
                f"Please verify this information is correct.\n\n"
                f"Register link: https://dashboard.vivaclubs.site/kiosk/register/"
            )
            try:
                LineService.push_text(to=line_user_id, text=confirm_message)
            except Exception as push_err:
                print(f"LINE registration confirmation push failed: {push_err}")

            serializer = LineUserSerializer(line_user)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(serializer.data, status=status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserStatusView(APIView):
    @extend_schema(
        summary="Get user locker status",
        description="Returns whether the user has an active (non-AVAILABLE) locker and its details.",
        parameters=[OpenApiParameter(name='line_user_id', location=OpenApiParameter.QUERY, required=True, type=str, description="LINE user ID")],
        responses={
            200: OpenApiResponse(description="Returns status (HAS_ACTIVE_LOCKER or NO_ACTIVE_LOCKER) and list of active lockers."),
            400: OpenApiResponse(description="line_user_id parameter missing."),
            404: OpenApiResponse(description="User not found."),
        },
        auth=[],
    )
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
        locker_ids = LockerLog.objects.filter(actor_id=line_user_id).values('locker_id')
        active_lockers = list(
            Locker.objects
            .filter(id__in=locker_ids)
            .exclude(status=Locker.Status.AVAILABLE)
            .order_by('building_id', 'local_id', 'id')
        )

        if not active_lockers:
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
        qs = Locker.objects.all().order_by('building_id', 'local_id', 'id')
        building_id = self.request.query_params.get('building_id')
        if building_id:
            qs = qs.filter(building_id=building_id)
        locker_status = self.request.query_params.get('status')
        if locker_status:
            qs = qs.filter(status=locker_status.upper())
        locker_type = self.request.query_params.get('type')
        if locker_type:
            qs = qs.filter(type=locker_type.upper())
        size = self.request.query_params.get('size')
        if size:
            qs = qs.filter(size=size.upper())
        return qs

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('update', 'partial_update'):
            return LockerUpdateSerializer
        return LockerSerializer

    def perform_update(self, serializer):
        locker = serializer.save()
        broadcast_locker_update(
            locker,
            action='ACTION_UPDATE',
            actor_id=_request_actor_id(self.request, default='admin'),
        )

    @extend_schema(
        summary="Book an available locker",
        description="Find and book an AVAILABLE locker by building, size, and type. Actor is derived from the authenticated JWT user.",
        responses={
            200: OpenApiResponse(description="Returns locker_id, qr_data, and passcode."),
            400: OpenApiResponse(description="Missing fields or no available locker found."),
        },
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticatedOrKiosk])
    def book(self, request):
        building_id = request.data.get('building_id')
        size = request.data.get('size')
        locker_type = request.data.get('type')

        if not all([building_id, size, locker_type]):
            return Response({'error': 'building_id, size, and type are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            locker = LockerService.book_locker(
                building_id,
                size.upper(),
                locker_type.upper(),
                actor_id=_actor_id(request),
            )
            return Response({
                'locker_id': locker.id,
                'qr_data': locker.qr_data,
                'passcode': locker.passcode
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Open a locker door",
        description="Unlock and open the door of a BOOKED or OCCUPIED locker.",
        responses={
            200: LockerSerializer,
            400: OpenApiResponse(description="Locker not found or invalid status."),
        },
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrKiosk])
    def open(self, request, pk=None):
        try:
            locker = LockerService.open_locker(locker_id=pk, actor_id=_actor_id(request))
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Confirm food deposit",
        description="Confirm that food has been placed in a BOOKED locker (door must be open). Transitions status to OCCUPIED.",
        responses={
            200: LockerSerializer,
            400: OpenApiResponse(description="Locker not found, wrong status, or door not open."),
        },
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticatedOrKiosk])
    def deposit(self, request, pk=None):
        try:
            locker = LockerService.confirm_deposit(locker_id=pk, actor_id=_actor_id(request))
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Verify QR code or passcode",
        description="Verify the customer's QR code or passcode and open the OCCUPIED locker for pickup.",
        request={"application/json": {"type": "object", "properties": {
            "qr_data": {"type": "string"},
            "passcode": {"type": "string"},
        }}},
        responses={
            200: LockerSerializer,
            400: OpenApiResponse(description="Invalid QR/passcode or locker not occupied."),
        },
    )
    @action(detail=False, methods=['post'], url_path='verify-qr', permission_classes=[IsAuthenticatedOrKiosk])
    def verify_qr(self, request):
        qr_data = request.data.get('qr_data')
        passcode = request.data.get('passcode')
        code = request.data.get('code')
        
        if code:
            if len(code) == 6 and code.isdigit():
                passcode = code
            else:
                qr_data = code
                
        try:
            locker = LockerService.verify_qr(
                qr_data=qr_data,
                passcode=passcode,
                actor_id=_actor_id(request, fallback='customer'),
            )
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Confirm customer pickup",
        description="Confirm that the customer has retrieved the food. Resets the locker to AVAILABLE.",
        responses={
            200: LockerSerializer,
            400: OpenApiResponse(description="Locker not found or not in OCCUPIED status."),
        },
    )
    @action(detail=True, methods=['post'], url_path='pickup', permission_classes=[IsAuthenticatedOrKiosk])
    def pickup(self, request, pk=None):
        actor_id = request.data.get('actor_id') or _actor_id(request, fallback='customer')
        try:
            locker = LockerService.pickup_locker(locker_id=pk, actor_id=actor_id)
            serializer = self.get_serializer(locker)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LineWebhookView(APIView):
    @extend_schema(
        summary="LINE Messaging API webhook",
        description="Receives webhook events from the LINE platform. Validates the HMAC-SHA256 X-Line-Signature header.",
        responses={
            200: OpenApiResponse(description="Webhook received and processed."),
            401: OpenApiResponse(description="Invalid or missing X-Line-Signature."),
        },
        auth=[],
    )
    def post(self, request):
        signature = request.headers.get('X-Line-Signature', '')
        body = request.body

        if not LineService.verify_signature(body, signature):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)

        events = request.data.get('events', [])
        for event in events:
            if event.get('type') == 'message':
                msg = event.get('message', {})
                if msg.get('type') == 'text':
                    text = msg.get('text', '').strip()
                    source = event.get('source', {})
                    user_id = source.get('userId')
                    
                    if user_id:
                        if text.lower().startswith('register'):
                            parts = text.split()
                            room_no = parts[1] if len(parts) > 1 else None
                            if room_no:
                                try:
                                    project = Project.objects.get_or_create(id='prj-001', defaults={'name': 'Project A', 'address': 'Default'})[0]
                                    building = Building.objects.get_or_create(id='bld-001', project=project, defaults={'name': 'Building 1'})[0]
                                    LineUser.objects.update_or_create(
                                        line_user_id=user_id,
                                        defaults={
                                            'project': project,
                                            'building': building,
                                            'room_no': room_no,
                                            'display_name': 'User'
                                        }
                                    )
                                    reply_text = f"✅ ลงทะเบียนผูกห้องพัก {room_no} สำเร็จเรียบร้อยแล้ว!"
                                except Exception as e:
                                    reply_text = f"❌ เกิดข้อผิดพลาดในการลงทะเบียน: {str(e)}"
                            else:
                                reply_text = "กรุณาระบุหมายเลขห้อง เช่น Register 101"
                        else:
                            reply_text = "พิมพ์คำว่า \"Register <หมายเลขห้อง>\" (เช่น Register 101) เพื่อผูกบัญชี LINE กับตู้ล็อกเกอร์และรับรหัสผ่านสำหรับเปิดตู้"
                        
                        try:
                            LineService.push_text(to=user_id, text=reply_text)
                        except Exception as e:
                            print(f"LINE push failed: {e}")

        return Response({'status': 'ok'}, status=status.HTTP_200_OK)



class LinePushView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Send LINE push message",
        description="Push a text message, an image, or both to a LINE user. Requires JWT authentication.",
        request={"application/json": {"type": "object", "properties": {
            "to": {"type": "string", "description": "LINE user ID of the recipient"},
            "message": {"type": "string", "description": "Text message to send"},
            "image_url": {"type": "string", "description": "Public URL of image to send"},
        }, "required": ["to"]}},
        responses={
            200: OpenApiResponse(description="Message sent successfully."),
            400: OpenApiResponse(description="Missing required fields."),
            401: OpenApiResponse(description="JWT authentication required."),
            500: OpenApiResponse(description="LINE API error."),
        },
    )
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


class LineNotifyView(APIView):
    permission_classes = [IsAuthenticatedOrKiosk]

    @extend_schema(
        summary="Lookup room and send LINE notification",
        description="Verify if a LINE user is registered for the specified room, and send a notification with PIN/QR.",
        request={"application/json": {"type": "object", "properties": {
            "room_no": {"type": "string"},
            "building_id": {"type": "string"},
            "locker_id": {"type": "string"},
        }, "required": ["room_no", "building_id", "locker_id"]}},
        responses={
            200: OpenApiResponse(description="Notification sent successfully."),
            400: OpenApiResponse(description="Invalid request or locker state."),
            404: OpenApiResponse(description="Room or locker not found."),
        },
        auth=[],
    )
    def post(self, request):
        room_no = request.data.get('room_no')
        building_id = request.data.get('building_id')
        locker_id = request.data.get('locker_id')

        if not all([room_no, building_id, locker_id]):
            return Response({'error': 'room_no, building_id, and locker_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Lookup LineUser for the room in this building
        try:
            line_user = LineUser.objects.filter(
                room_no=room_no, 
                building_id=building_id,
                line_user_id__startswith='U'
            ).first()
            if not line_user:
                line_user = LineUser.objects.filter(room_no=room_no, building_id=building_id).first()
            if not line_user:
                return Response({'error': 'ไม่พบข้อมูลลูกบ้านที่ลงทะเบียนห้องนี้ในตึกนี้'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Get locker details
        try:
            locker = Locker.objects.get(id=locker_id)
        except Locker.DoesNotExist:
            return Response({'error': 'ไม่พบตู้นี้ในระบบ'}, status=status.HTTP_404_NOT_FOUND)

        # 3. Construct message and QR code
        message = (
            f"🔔 มีอาหารมาส่งใหม่สำเร็จเรียบร้อยแล้ว!\n\n"
            f"📍 ตึก: {locker.building.name}\n"
            f"📦 ตู้หมายเลข: {locker.local_id}\n"
            f"🔑 รหัส PIN สำหรับเปิดตู้: {locker.passcode}\n\n"
            f"กรุณาใช้รหัส PIN 6 หลัก หรือสแกนภาพ QR Code ด้านล่างเพื่อรับอาหารของคุณ"
        )
        
        # Build QR code data
        qr_data = locker.qr_data or locker.passcode
        qr_image_url = f"https://quickchart.io/qr?text={qr_data}&size=400&margin=2"

        try:
            # 4. Send via LineService
            LineService.push_text_and_image(
                to=line_user.line_user_id,
                text=message,
                image_url=qr_image_url
            )
            return Response({'status': 'ok', 'display_name': line_user.display_name}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'ไม่สามารถส่งข้อความ LINE ได้: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

        lockers = list(queryset)
        return Response({
            'command': 'list',
            'count': len(lockers),
            'lockers': LockerSerializer(lockers, many=True).data,
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
