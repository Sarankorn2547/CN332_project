import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from foodlocker.models import Project, Building, Room, LineUser, Locker

# log in page
@require_GET
def login_page(request):
    return render(request, 'kiosk/login.html')

# ============================================================================
# Main Kiosk Interface
# ============================================================================
@require_GET
def kiosk_home(request):
    """
    Kiosk home screen - user type selection
    Displays three buttons: Rider, Customer, Security Guard
    """
    building_id = KIOSK_BUILDING_ID
    try:
        building = Building.objects.get(id=building_id)
        project = building.project
    except Building.DoesNotExist:
        building = None
        project = None

    return render(request, 'kiosk/home.html', {
        'building': building,
        'project': project
    })


# ============================================================================
# Registration Page
# ============================================================================

@require_GET
def registration_page(request):
    projects = Project.objects.all().order_by('name')
    liff_id = getattr(settings, 'LINE_LIFF_ID', '')
    return render(request, 'registration/register.html', {
        'projects': projects,
        'liff_id': liff_id
    })


# ============================================================================
# Rider Flow Views
# ============================================================================

KIOSK_BUILDING_ID = 'bld-001'

@require_GET
def rider_select_size(request):
    return render(request, 'kiosk/rider/select_size.html', {'building_id': KIOSK_BUILDING_ID})

@require_GET
def rider_select_method(request):
    return render(request, 'kiosk/rider/select_method.html')

@require_GET
def rider_input_room(request):
    return render(request, 'kiosk/rider/input_room.html', {'building_id': KIOSK_BUILDING_ID})

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
    SIZE_META = {
        'S': '25×30 cm',
        'M': '35×40 cm', 
        'L': '45×50 cm',
        'XL': '55×60 cm',
    }
    sizes_data = []
    import time
    current_time = int(time.time())
    for code, dimensions in SIZE_META.items():
        if building_id:
            all_avail = Locker.objects.filter(
                building_id=building_id, size=code, status='AVAILABLE'
            )
            count = 0
            for l in all_avail:
                reserved_at = (l.metadata or {}).get("reserved_at", 0)
                if current_time - reserved_at > 120:
                    count += 1
        else:
            count = 0
        sizes_data.append({'code': code, 'dimensions': dimensions, 'available': count})
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({'sizes': sizes_data})
    return render(request, 'fragments/locker_sizes.html', {'sizes': sizes_data})

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
