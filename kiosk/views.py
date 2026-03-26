from django.shortcuts import render
from django.http import HttpResponse


# ============================================================================
# Main Kiosk Interface
# ============================================================================

def kiosk_home(request):
    """
    Kiosk home screen - user type selection
    Displays three buttons: Rider, Customer, Security Guard
    """
    return render(request, 'kiosk/home.html')


# ============================================================================
# Registration Page
# ============================================================================

def registration_page(request):
    """
    User registration page with LINE LIFF integration
    Allows residents to register their account through LINE
    """
    return render(request, 'registration/register.html')


# ============================================================================
# Rider Flow Views
# ============================================================================

def rider_select_size(request):
    """
    Rider Step 1: Select locker size
    Displays available locker sizes (S, M, L, XL) with availability counts
    """
    return render(request, 'kiosk/rider/select_size.html')


def rider_qr_display(request):
    """
    Rider Step 2: Display QR code and PIN
    Shows the generated QR code and 4-digit PIN for customer
    """
    return render(request, 'kiosk/rider/qr_display.html')


def rider_confirm(request):
    """
    Rider Step 3: Confirm photo sent to customer
    Confirmation dialog before opening locker
    """
    return render(request, 'kiosk/rider/confirm.html')


def rider_deposit(request):
    """
    Rider Step 4: Deposit food and take proof photo
    Camera interface for taking proof photo of food in locker
    """
    return render(request, 'kiosk/rider/deposit.html')


def rider_success(request):
    """
    Rider completion screen
    Shows transaction summary and auto-redirects to home
    """
    return render(request, 'kiosk/rider/success.html')


# ============================================================================
# Customer Flow Views
# ============================================================================

def customer_method_select(request):
    """
    Customer: Choose authentication method
    Options: QR scan or PIN entry
    """
    return render(request, 'kiosk/customer/method_select.html')


def customer_qr_scan(request):
    """
    Customer: QR code scanner
    Camera interface for scanning QR code
    """
    return render(request, 'kiosk/customer/qr_scan.html')


def customer_pin_entry(request):
    """
    Customer: PIN entry keypad
    Numeric keypad for entering 4-digit PIN
    """
    return render(request, 'kiosk/customer/pin_entry.html')


def customer_success(request):
    """
    Customer completion screen
    Shows locker opened successfully and transaction details
    """
    return render(request, 'kiosk/customer/success.html')


# ============================================================================
# Security Flow Views
# ============================================================================

def security_master_access(request):
    """
    Security guard master access
    Master QR code scanner for emergency access
    """
    return render(request, 'kiosk/security/master_access.html')


# ============================================================================
# HTMX Endpoints (Return HTML Fragments)
# ============================================================================

def htmx_get_buildings(request):
    """
    HTMX endpoint: Get buildings for selected project
    Returns <option> elements for building dropdown
    """
    project_id = request.GET.get('project_id')
    # TODO: Fetch buildings from database
    # buildings = Building.objects.filter(project_id=project_id)
    return render(request, 'fragments/building_options.html', {
        'buildings': []  # Placeholder
    })


def htmx_get_rooms(request):
    """
    HTMX endpoint: Get rooms for selected building
    Returns <option> elements for room dropdown
    """
    building_id = request.GET.get('building_id')
    # TODO: Fetch rooms from database
    # rooms = Room.objects.filter(building_id=building_id)
    return render(request, 'fragments/room_options.html', {
        'rooms': []  # Placeholder
    })


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
