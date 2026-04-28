from django.test import TestCase
from django.urls import reverse, resolve
from . import views


class URLRoutingTests(TestCase):
    """
    Test suite for URL routing and namespacing.
    Validates: Requirements 1.6
    """

    def test_home_url_resolves(self):
        """Test that kiosk home URL resolves correctly"""
        url = reverse('kiosk:home')
        self.assertEqual(url, '/kiosk/')
        self.assertEqual(resolve(url).func, views.kiosk_home)

    def test_register_url_resolves(self):
        """Test that registration URL resolves correctly"""
        url = reverse('kiosk:register')
        self.assertEqual(url, '/kiosk/register/')
        self.assertEqual(resolve(url).func, views.registration_page)

    # Rider flow URL tests
    def test_rider_select_size_url_resolves(self):
        """Test that rider select size URL resolves correctly"""
        url = reverse('kiosk:rider_select_size')
        self.assertEqual(url, '/kiosk/rider/select-size/')
        self.assertEqual(resolve(url).func, views.rider_select_size)

    def test_rider_qr_display_url_resolves(self):
        """Test that rider QR display URL resolves correctly"""
        url = reverse('kiosk:rider_qr_display')
        self.assertEqual(url, '/kiosk/rider/qr-display/')
        self.assertEqual(resolve(url).func, views.rider_qr_display)

    def test_rider_confirm_url_resolves(self):
        """Test that rider confirm URL resolves correctly"""
        url = reverse('kiosk:rider_confirm')
        self.assertEqual(url, '/kiosk/rider/confirm/')
        self.assertEqual(resolve(url).func, views.rider_confirm)

    def test_rider_deposit_url_resolves(self):
        """Test that rider deposit URL resolves correctly"""
        url = reverse('kiosk:rider_deposit')
        self.assertEqual(url, '/kiosk/rider/deposit/')
        self.assertEqual(resolve(url).func, views.rider_deposit)

    def test_rider_success_url_resolves(self):
        """Test that rider success URL resolves correctly"""
        url = reverse('kiosk:rider_success')
        self.assertEqual(url, '/kiosk/rider/success/')
        self.assertEqual(resolve(url).func, views.rider_success)

    # Customer flow URL tests
    def test_customer_method_select_url_resolves(self):
        """Test that customer method select URL resolves correctly"""
        url = reverse('kiosk:customer_method_select')
        self.assertEqual(url, '/kiosk/customer/method-select/')
        self.assertEqual(resolve(url).func, views.customer_method_select)

    def test_customer_qr_scan_url_resolves(self):
        """Test that customer QR scan URL resolves correctly"""
        url = reverse('kiosk:customer_qr_scan')
        self.assertEqual(url, '/kiosk/customer/qr-scan/')
        self.assertEqual(resolve(url).func, views.customer_qr_scan)

    def test_customer_pin_entry_url_resolves(self):
        """Test that customer PIN entry URL resolves correctly"""
        url = reverse('kiosk:customer_pin_entry')
        self.assertEqual(url, '/kiosk/customer/pin-entry/')
        self.assertEqual(resolve(url).func, views.customer_pin_entry)

    def test_customer_success_url_resolves(self):
        """Test that customer success URL resolves correctly"""
        url = reverse('kiosk:customer_success')
        self.assertEqual(url, '/kiosk/customer/success/')
        self.assertEqual(resolve(url).func, views.customer_success)

    # Security flow URL tests
    def test_security_master_access_url_resolves(self):
        """Test that security master access URL resolves correctly"""
        url = reverse('kiosk:security_master_access')
        self.assertEqual(url, '/kiosk/security/master-access/')
        self.assertEqual(resolve(url).func, views.security_master_access)

    # HTMX endpoint URL tests
    def test_htmx_buildings_url_resolves(self):
        """Test that HTMX buildings endpoint URL resolves correctly"""
        url = reverse('kiosk:htmx_buildings')
        self.assertEqual(url, '/kiosk/htmx/buildings/')
        self.assertEqual(resolve(url).func, views.htmx_get_buildings)

    def test_htmx_rooms_url_resolves(self):
        """Test that HTMX rooms endpoint URL resolves correctly"""
        url = reverse('kiosk:htmx_rooms')
        self.assertEqual(url, '/kiosk/htmx/rooms/')
        self.assertEqual(resolve(url).func, views.htmx_get_rooms)

    def test_htmx_locker_sizes_url_resolves(self):
        """Test that HTMX locker sizes endpoint URL resolves correctly"""
        url = reverse('kiosk:htmx_locker_sizes')
        self.assertEqual(url, '/kiosk/htmx/locker-sizes/')
        self.assertEqual(resolve(url).func, views.htmx_get_locker_sizes)

    def test_htmx_qr_display_url_resolves(self):
        """Test that HTMX QR display endpoint URL resolves correctly"""
        url = reverse('kiosk:htmx_qr_display')
        self.assertEqual(url, '/kiosk/htmx/qr-display/')
        self.assertEqual(resolve(url).func, views.htmx_qr_display)

    def test_htmx_locker_status_url_resolves(self):
        """Test that HTMX locker status endpoint URL resolves correctly"""
        url = reverse('kiosk:htmx_locker_status')
        self.assertEqual(url, '/kiosk/htmx/locker-status/')
        self.assertEqual(resolve(url).func, views.htmx_locker_status)


class URLNamespacingTests(TestCase):
    """
    Test suite for URL namespacing functionality.
    Validates: Requirements 1.6
    """

    def test_kiosk_namespace_exists(self):
        """Test that kiosk namespace is properly configured"""
        # This will raise NoReverseMatch if namespace doesn't exist
        url = reverse('kiosk:home')
        self.assertIsNotNone(url)

    def test_all_rider_urls_use_namespace(self):
        """Test that all rider URLs work with kiosk namespace"""
        rider_urls = [
            'rider_select_size',
            'rider_qr_display',
            'rider_confirm',
            'rider_deposit',
            'rider_success',
        ]
        for url_name in rider_urls:
            with self.subTest(url_name=url_name):
                url = reverse(f'kiosk:{url_name}')
                self.assertTrue(url.startswith('/kiosk/rider/'))

    def test_all_customer_urls_use_namespace(self):
        """Test that all customer URLs work with kiosk namespace"""
        customer_urls = [
            'customer_method_select',
            'customer_qr_scan',
            'customer_pin_entry',
            'customer_success',
        ]
        for url_name in customer_urls:
            with self.subTest(url_name=url_name):
                url = reverse(f'kiosk:{url_name}')
                self.assertTrue(url.startswith('/kiosk/customer/'))

    def test_all_htmx_urls_use_namespace(self):
        """Test that all HTMX endpoint URLs work with kiosk namespace"""
        htmx_urls = [
            'htmx_buildings',
            'htmx_rooms',
            'htmx_locker_sizes',
            'htmx_qr_display',
            'htmx_locker_status',
        ]
        for url_name in htmx_urls:
            with self.subTest(url_name=url_name):
                url = reverse(f'kiosk:{url_name}')
                self.assertTrue(url.startswith('/kiosk/htmx/'))


class URLReverseTests(TestCase):
    """
    Test suite for reverse URL lookups.
    Validates: Requirements 1.6
    """

    def test_reverse_home_url(self):
        """Test reverse lookup for home URL"""
        url = reverse('kiosk:home')
        self.assertEqual(url, '/kiosk/')

    def test_reverse_register_url(self):
        """Test reverse lookup for register URL"""
        url = reverse('kiosk:register')
        self.assertEqual(url, '/kiosk/register/')

    def test_reverse_all_rider_urls(self):
        """Test reverse lookup for all rider flow URLs"""
        expected_urls = {
            'rider_select_size': '/kiosk/rider/select-size/',
            'rider_qr_display': '/kiosk/rider/qr-display/',
            'rider_confirm': '/kiosk/rider/confirm/',
            'rider_deposit': '/kiosk/rider/deposit/',
            'rider_success': '/kiosk/rider/success/',
        }
        for url_name, expected_path in expected_urls.items():
            with self.subTest(url_name=url_name):
                url = reverse(f'kiosk:{url_name}')
                self.assertEqual(url, expected_path)

    def test_reverse_all_customer_urls(self):
        """Test reverse lookup for all customer flow URLs"""
        expected_urls = {
            'customer_method_select': '/kiosk/customer/method-select/',
            'customer_qr_scan': '/kiosk/customer/qr-scan/',
            'customer_pin_entry': '/kiosk/customer/pin-entry/',
            'customer_success': '/kiosk/customer/success/',
        }
        for url_name, expected_path in expected_urls.items():
            with self.subTest(url_name=url_name):
                url = reverse(f'kiosk:{url_name}')
                self.assertEqual(url, expected_path)

    def test_reverse_security_url(self):
        """Test reverse lookup for security master access URL"""
        url = reverse('kiosk:security_master_access')
        self.assertEqual(url, '/kiosk/security/master-access/')

    def test_reverse_all_htmx_urls(self):
        """Test reverse lookup for all HTMX endpoint URLs"""
        expected_urls = {
            'htmx_buildings': '/kiosk/htmx/buildings/',
            'htmx_rooms': '/kiosk/htmx/rooms/',
            'htmx_locker_sizes': '/kiosk/htmx/locker-sizes/',
            'htmx_qr_display': '/kiosk/htmx/qr-display/',
            'htmx_locker_status': '/kiosk/htmx/locker-status/',
        }
        for url_name, expected_path in expected_urls.items():
            with self.subTest(url_name=url_name):
                url = reverse(f'kiosk:{url_name}')
                self.assertEqual(url, expected_path)
