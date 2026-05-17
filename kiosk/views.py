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
    is_friend = request.GET.get('is_friend', 'true')
    
    # Retrieve bot basic ID from settings or default to '@166qwhfr'
    bot_basic_id = getattr(settings, 'LINE_BOT_BASIC_ID', '@166qwhfr')
    bot_link_id = bot_basic_id.replace('@', '')

    return render(request, 'registration/register.html', {
        'projects': projects,
        'liff_id': liff_id,
        'is_friend': is_friend,
        'bot_link_id': bot_link_id,
    })


@require_GET
def line_login_redirect(request):
    import urllib.parse
    from django.shortcuts import redirect
    client_id = getattr(settings, 'LINE_CHANNEL_ID', '2009130619')
    redirect_uri = 'https://dashboard.vivaclubs.site/kiosk/register/callback/'
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': 'cn332_state_secret',
        'scope': 'profile openid',
        'bot_prompt': 'aggressive',
    }
    
    url = 'https://access.line.me/oauth2/v2.1/authorize?' + urllib.parse.urlencode(params)
    return redirect(url)


@require_GET
def line_login_callback(request):
    import urllib.parse
    import requests
    from django.shortcuts import redirect
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        return HttpResponse("LINE Login failed: Authorization code not provided.", status=400)
        
    client_id = getattr(settings, 'LINE_CHANNEL_ID', '2009130619')
    client_secret = getattr(settings, 'LINE_LOGIN_CHANNEL_SECRET', '055835d34d26874891f4baa9135cdf91')
    redirect_uri = 'https://dashboard.vivaclubs.site/kiosk/register/callback/'
    
    # Exchange code for access token
    token_url = 'https://api.line.me/oauth2/v2.1/token'
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        resp = requests.post(token_url, data=data, headers=headers)
        if not resp.ok:
            return HttpResponse(f"LINE Token Exchange Failed: {resp.status_code} - {resp.text}", status=400)
        token_data = resp.json()
        access_token = token_data.get('access_token')
        
        # Fetch LINE profile using access token
        profile_url = 'https://api.line.me/v2/profile'
        profile_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        profile_resp = requests.get(profile_url, headers=profile_headers)
        profile_resp.raise_for_status()
        profile_data = profile_resp.json()
        
        line_user_id = profile_data.get('userId')
        display_name = profile_data.get('displayName')

        # Check friendship status with the bot
        friend_flag = False
        try:
            friendship_url = 'https://api.line.me/friendship/v2/status'
            friendship_headers = {
                'Authorization': f'Bearer {access_token}'
            }
            friendship_resp = requests.get(friendship_url, headers=friendship_headers)
            print(f"[Friendship API Response] Status: {friendship_resp.status_code}, Body: {friendship_resp.text}")
            if friendship_resp.ok:
                friend_flag = friendship_resp.json().get('friendFlag', False)
        except Exception as friendship_err:
            print(f"Friendship status check failed: {friendship_err}")
        
        # Redirect to the register page with query parameters
        is_friend_str = 'true' if friend_flag else 'false'
        register_url = f'/kiosk/register/?line_user_id={urllib.parse.quote(line_user_id)}&display_name={urllib.parse.quote(display_name)}&is_friend={is_friend_str}'
        return redirect(register_url)
        
    except Exception as e:
        return HttpResponse(f"LINE Login Error: {str(e)}", status=500)


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
