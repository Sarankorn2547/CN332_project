from django.urls import path
from . import views

app_name = 'kiosk'

urlpatterns = [
    # Main kiosk interface
    path('', views.kiosk_home, name='home'),
    
    # Registration page
    path('register/', views.registration_page, name='register'),
    
    # Rider flow URLs
    path('rider/select-size/', views.rider_select_size, name='rider_select_size'),
    path('rider/qr-display/', views.rider_qr_display, name='rider_qr_display'),
    path('rider/confirm/', views.rider_confirm, name='rider_confirm'),
    path('rider/deposit/', views.rider_deposit, name='rider_deposit'),
    path('rider/success/', views.rider_success, name='rider_success'),
    
    # Customer flow URLs
    path('customer/method-select/', views.customer_method_select, name='customer_method_select'),
    path('customer/qr-scan/', views.customer_qr_scan, name='customer_qr_scan'),
    path('customer/pin-entry/', views.customer_pin_entry, name='customer_pin_entry'),
    path('customer/success/', views.customer_success, name='customer_success'),
    
    # Security flow URLs
    path('security/master-access/', views.security_master_access, name='security_master_access'),
    
    # HTMX endpoints for dynamic content
    path('htmx/buildings/', views.htmx_get_buildings, name='htmx_buildings'),
    path('htmx/rooms/', views.htmx_get_rooms, name='htmx_rooms'),
    path('htmx/locker-sizes/', views.htmx_get_locker_sizes, name='htmx_locker_sizes'),
    path('htmx/qr-display/', views.htmx_qr_display, name='htmx_qr_display'),
    path('htmx/locker-status/', views.htmx_locker_status, name='htmx_locker_status'),

    # ── API endpoints ───────────────────────────────────
    path('api/lockers/book/',                views.api_book_locker,      name='api_book_locker'),
    path('api/lockers/<str:locker_id>/open/',    views.api_open_locker,  name='api_open_locker'),
    path('api/lockers/<str:locker_id>/deposit/', views.api_deposit,      name='api_deposit'),
    path('api/lockers/verify-qr/',           views.api_verify_qr,        name='api_verify_qr'),
    path('api/users/register/',              views.api_register_user,    name='api_register_user'),
]
