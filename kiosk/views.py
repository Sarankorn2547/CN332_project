import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from foodlocker.models import Project, Building, Room, LineUser


# ============================================================================
# Main Kiosk Interface
# ============================================================================
@require_GET
def kiosk_home(request):
    """
    Kiosk home screen - user type selection
    Displays three buttons: Rider, Customer, Security Guard
    """
    return render(request, 'kiosk/home.html')


# ============================================================================
# Registration Page
# ============================================================================

@require_GET
def registration_page(request):
    projects = Project.objects.all().order_by('name')
    return render(request, 'registration/register.html', {'projects': projects})


# ============================================================================
# Rider Flow Views
# ============================================================================

@require_GET
def rider_select_size(request):
    """
    Rider Step 1: Select locker size
    Displays available locker sizes (S, M, L, XL) with availability counts
    """
    return render(request, 'kiosk/rider/select_size.html')

@require_GET
def rider_qr_display(request):
    """
    Rider Step 2: Display QR code and PIN
    Shows the generated QR code and 4-digit PIN for customer
    """
    return render(request, 'kiosk/rider/qr_display.html')

@require_GET
def rider_confirm(request):
    """
    Rider Step 3: Confirm photo sent to customer
    Confirmation dialog before opening locker
    """
    return render(request, 'kiosk/rider/confirm.html')

@require_GET
def rider_deposit(request):
    """
    Rider Step 4: Deposit food and take proof photo
    Camera interface for taking proof photo of food in locker
    """
    return render(request, 'kiosk/rider/deposit.html')

@require_GET
def rider_success(request):
    """
    Rider completion screen
    Shows transaction summary and auto-redirects to home
    """
    return render(request, 'kiosk/rider/success.html')


# ============================================================================
# Customer Flow Views
# ============================================================================
@require_GET
def customer_method_select(request):
    """
    Customer: Choose authentication method
    Options: QR scan or PIN entry
    """
    return render(request, 'kiosk/customer/method_select.html')

@require_GET
def customer_qr_scan(request):
    """
    Customer: QR code scanner
    Camera interface for scanning QR code
    """
    return render(request, 'kiosk/customer/qr_scan.html')


@require_GET
def customer_pin_entry(request):
    """
    Customer: PIN entry keypad
    Numeric keypad for entering 4-digit PIN
    """
    return render(request, 'kiosk/customer/pin_entry.html')

@require_GET
def customer_success(request):
    """
    Customer completion screen
    Shows locker opened successfully and transaction details
    """
    return render(request, 'kiosk/customer/success.html')


# ============================================================================
# Security Flow Views
# ============================================================================

@require_GET
def security_master_access(request):
    """
    Security guard master access
    Master QR code scanner for emergency access
    """
    return render(request, 'kiosk/security/master_access.html')


# ============================================================================
# HTMX Endpoints (Return HTML Fragments)
# ============================================================================

@require_GET
def htmx_get_buildings(request):
    project_id = request.GET.get('project_id')
    buildings = Building.objects.filter(project_id=project_id).order_by('name') if project_id else []
    return render(request, 'fragments/building_options.html', {'buildings': buildings})

@require_GET
def htmx_get_rooms(request):
    building_id = request.GET.get('building_id')
    rooms = Room.objects.filter(building_id=building_id).order_by('floor', 'unit_number') if building_id else []
    return render(request, 'fragments/room_options.html', {'rooms': rooms})

@require_GET
def htmx_get_locker_sizes(request):
    """
    HTMX endpoint: Get available locker sizes
    Returns HTML cards showing available locker sizes with counts
    """
    building_id = request.GET.get('building_id')
    # TODO: Fetch locker availability from database
    # availability = get_locker_availability(building_id)
    return render(request, 'fragments/locker_sizes.html', {
        'sizes': []  # Placeholder
    })

@require_POST
def htmx_qr_display(request):
    """
    HTMX endpoint: Generate and display QR code
    Returns QR code display HTML after booking
    """
    if request.method == 'POST':
        # TODO: Book locker and generate QR code
        # booking = book_locker(size, type, building_id)
        return render(request, 'fragments/qr_display.html', {
            'qr_data': '',  # Placeholder
            'passcode': '',  # Placeholder
            'locker_id': ''  # Placeholder
        })
    return HttpResponse(status=405)  # Method not allowed

@require_GET
def htmx_locker_status(request):
    """
    HTMX endpoint: Get current locker status
    Returns status indicator HTML for polling fallback
    """
    locker_id = request.GET.get('locker_id')
    # TODO: Fetch locker status from database
    # locker = Locker.objects.get(id=locker_id)
    return render(request, 'fragments/locker_status.html', {
        'locker': None  # Placeholder
    })
# ============================================================
# API Endpoints (Sprint 3-4) - stub สำหรับเชื่อม frontend
# TODO: เชื่อม logic จริงเข้ากับ database/hardware
# ============================================================

@csrf_exempt   # ชั่วคราวระหว่าง dev — production ต้องส่ง CSRF token จาก frontend
@require_POST
def api_book_locker(request):
    """POST /kiosk/api/lockers/book/
    รับ: { size, type, building_id }
    ส่ง: { locker_id, pin, qr_url, booking_id }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    size = data.get('size')
    locker_type = data.get('type')
    building_id = data.get('building_id')

    # TODO: เรียก service จองตู้จริง เช่น
    # locker = LockerService.book(size, locker_type, building_id)

    return JsonResponse({
        'locker_id': 'M-12',
        'pin': '1234',
        'qr_url': '/static/img/sample-qr.png',
        'booking_id': 'BK-001',
    })


@csrf_exempt
@require_POST
def api_open_locker(request, locker_id):
    """POST /kiosk/api/lockers/<locker_id>/open/
    ส่งคำสั่งเปิดตู้ไปที่ hardware
    """
    # TODO: integrate กับ hardware controller
    return JsonResponse({'status': 'opened', 'locker_id': locker_id})


@csrf_exempt
@require_POST
def api_deposit(request, locker_id):
    """POST /kiosk/api/lockers/<locker_id>/deposit/
    รับ: { photo: base64-string }
    บันทึกรูปยืนยันและอัปเดตสถานะ booking เป็น 'deposited'
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    photo_b64 = data.get('photo', '')

    # TODO: decode base64, save เป็นไฟล์, update booking status
    return JsonResponse({'status': 'deposited', 'locker_id': locker_id})


@csrf_exempt
@require_POST
def api_verify_qr(request):
    """POST /kiosk/api/lockers/verify-qr/
    รับ: { code }   # อาจเป็น QR string หรือ PIN 4 หลัก
    ตรวจสอบว่าตรงกับ booking ที่ active อยู่หรือไม่
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    code = data.get('code')

    # TODO: query booking จาก DB ตาม code
    return JsonResponse({
        'valid': True,
        'locker_id': 'M-12',
        'deposit_time': '2026-04-26T10:30:00Z',
    })


@csrf_exempt
@require_POST
def api_register_user(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)

    line_user_id = data.get('line_user_id')
    project_id = data.get('project_id')
    building_id = data.get('building_id')
    room_no = data.get('room_no')
    display_name = data.get('display_name')

    if not all([line_user_id, project_id, building_id, room_no, display_name]):
        return JsonResponse({'detail': 'กรุณากรอกข้อมูลให้ครบทุกช่อง'}, status=400)

    if LineUser.objects.filter(line_user_id=line_user_id).exists():
        return JsonResponse({'detail': 'ผู้ใช้นี้ลงทะเบียนแล้ว'}, status=400)

    try:
        project = Project.objects.get(id=project_id)
        building = Building.objects.get(id=building_id, project=project)
    except Project.DoesNotExist:
        return JsonResponse({'detail': 'ไม่พบโครงการ'}, status=404)
    except Building.DoesNotExist:
        return JsonResponse({'detail': 'ไม่พบอาคาร'}, status=404)

    LineUser.objects.create(
        line_user_id=line_user_id,
        project=project,
        building=building,
        room_no=room_no,
        display_name=display_name,
    )
    return JsonResponse({'status': 'registered'})
