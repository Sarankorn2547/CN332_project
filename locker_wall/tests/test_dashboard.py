from django.test import TestCase
from django.contrib.auth.models import User


class DashboardViewTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff_user', password='pass', is_staff=True
        )
        self.anon_url = '/locker/dashboard/'

    def test_returns_200_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.anon_url)
        self.assertEqual(response.status_code, 200)

    def test_redirects_anonymous(self):
        response = self.client.get(self.anon_url)
        self.assertEqual(response.status_code, 302)

    def test_redirect_target_is_login(self):
        response = self.client.get(self.anon_url)
        self.assertIn('/login', response['Location'])

    def test_has_stat_cards(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.anon_url)
        content = response.content.decode()
        self.assertIn('stat-card', content)
        for label in ('Total', 'Available', 'Occupied', 'Locked', 'Open'):
            self.assertIn(label, content)

    def test_has_four_tab_labels(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.anon_url)
        content = response.content.decode()
        for tab in ('Locker Overview', 'Logs', 'Reset Controls', 'LINE Push'):
            self.assertIn(tab, content)

    def test_has_alpine_dashboard_component(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.anon_url)
        self.assertIn(b'x-data="dashboard"', response.content)
