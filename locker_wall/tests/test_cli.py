from django.test import TestCase
from django.contrib.auth.models import User


class CLIViewTests(TestCase):

    def setUp(self):
        self.staff = User.objects.create_user(
            username='staff_user', password='pass', is_staff=True
        )
        self.url = '/locker/cli/'

    def test_returns_200_for_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_redirects_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_has_terminal_prompt(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertIn(b'foodlocker@admin', response.content)

    def test_has_alpine_terminal_component(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        # x-data value starts with terminal( — CSRF token follows
        self.assertIn(b'x-data="terminal(', response.content)

    def test_loads_jetbrains_mono_font(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.url)
        self.assertIn(b'JetBrains Mono', response.content)
