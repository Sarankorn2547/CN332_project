import json
from django.test import TestCase
from django.contrib.auth.models import User
from foodlocker.models import Project, Building, Locker


def _make_fixtures():
    """Return (project, building, locker) test objects."""
    project = Project.objects.create(
        id='prj-test', name='Test Project', address='123 Test St'
    )
    building = Building.objects.create(
        id='bld-test', project=project, name='Building A'
    )
    locker = Locker.objects.create(
        id='lck-test',
        building=building,
        local_id='1',
        size='M',
        status='AVAILABLE',
        type='FOOD',
        passcode='',
        qr_data='',
        is_door_open=False,
        has_object=False,
        is_locked=True,
    )
    return project, building, locker


class LockerOpenEndpointTests(TestCase):

    def setUp(self):
        _, _, self.locker = _make_fixtures()

    def test_open_url_is_registered(self):
        """POST to open/ must resolve — any status except 404 is acceptable."""
        response = self.client.post(
            f'/api/lockers/{self.locker.id}/open/',
            data='{}',
            content_type='application/json',
        )
        self.assertNotEqual(response.status_code, 404)


class SystemResetEndpointTests(TestCase):

    def setUp(self):
        _, self.building, self.locker = _make_fixtures()

    def test_reset_single_locker_returns_200(self):
        response = self.client.post(
            '/api/system/reset/',
            data=json.dumps({'scope': 'locker', 'locker_id': self.locker.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_all_returns_200(self):
        response = self.client.post(
            '/api/system/reset/',
            data=json.dumps({'scope': 'all'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_by_building_returns_200(self):
        response = self.client.post(
            '/api/system/reset/',
            data=json.dumps({'scope': 'building', 'building_id': self.building.id}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_invalid_scope_returns_400(self):
        response = self.client.post(
            '/api/system/reset/',
            data=json.dumps({'scope': 'unknown'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_reset_locker_missing_id_returns_400(self):
        response = self.client.post(
            '/api/system/reset/',
            data=json.dumps({'scope': 'locker'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class ReadOnlyAPITests(TestCase):

    def setUp(self):
        _make_fixtures()

    def test_locker_logs_returns_200(self):
        response = self.client.get('/api/locker-logs/')
        self.assertEqual(response.status_code, 200)

    def test_buildings_returns_200(self):
        response = self.client.get('/api/buildings/')
        self.assertEqual(response.status_code, 200)

    def test_lockers_list_returns_200(self):
        response = self.client.get('/api/lockers/')
        self.assertEqual(response.status_code, 200)
