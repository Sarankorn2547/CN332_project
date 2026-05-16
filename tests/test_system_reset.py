import pytest
from django.urls import reverse

from foodlocker.models import Building, Locker, LockerLog, Project


def _get_token(client, line_user):
    resp = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    return resp.data['access']


def _auth(line_user, client):
    return {'HTTP_AUTHORIZATION': f'Bearer {_get_token(client, line_user)}'}


def _dirty_locker(locker):
    locker.status = Locker.Status.OCCUPIED
    locker.passcode = '123456'
    locker.qr_data = 'qr-token'
    locker.is_door_open = True
    locker.has_object = True
    locker.is_locked = False
    locker.deposit_start_time = 1710000000
    locker.save()
    return locker


def _create_dirty_locker(locker_id, building, local_id='2'):
    return _dirty_locker(Locker.objects.create(
        id=locker_id,
        building=building,
        local_id=local_id,
        size='M',
        status=Locker.Status.AVAILABLE,
        type='FOOD',
        passcode='',
        qr_data='',
        is_door_open=False,
        has_object=False,
        is_locked=True,
    ))


def _assert_reset(locker):
    locker.refresh_from_db()
    assert locker.status == Locker.Status.AVAILABLE
    assert locker.passcode == ''
    assert locker.qr_data == ''
    assert locker.is_door_open is False
    assert locker.has_object is False
    assert locker.is_locked is True
    assert locker.deposit_start_time is None


@pytest.mark.django_db
def test_system_reset_requires_authentication(client, locker):
    response = client.post(
        '/api/system/reset/',
        data={'scope': 'ALL'},
        content_type='application/json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_system_reset_locker_scope_resets_single_locker(client, locker, line_user):
    _dirty_locker(locker)

    response = client.post(
        '/api/system/reset/',
        data={'scope': 'locker', 'locker_id': locker.id},
        content_type='application/json',
        **_auth(line_user, client),
    )

    assert response.status_code == 200
    assert response.data['scope'] == 'LOCKER'
    assert response.data['reset_count'] == 1
    assert response.data['locker_ids'] == [locker.id]
    _assert_reset(locker)

    log = LockerLog.objects.get(locker=locker, action='ACTION_RESET')
    assert log.actor_id == line_user.line_user_id
    assert log.metadata == {'scope': 'LOCKER', 'locker_id': locker.id}


@pytest.mark.django_db
def test_system_reset_building_scope_resets_only_building_lockers(client, project, building, line_user):
    first = _create_dirty_locker('lck-001', building, local_id='1')
    second = _create_dirty_locker('lck-002', building, local_id='2')
    other_building = Building.objects.create(id='bld-002', project=project, name='Building B')
    other = _create_dirty_locker('lck-003', other_building, local_id='3')

    response = client.post(
        '/api/system/reset/',
        data={'scope': 'BUILDING', 'building_id': building.id},
        content_type='application/json',
        **_auth(line_user, client),
    )

    assert response.status_code == 200
    assert response.data['scope'] == 'BUILDING'
    assert response.data['reset_count'] == 2
    assert set(response.data['locker_ids']) == {first.id, second.id}
    _assert_reset(first)
    _assert_reset(second)

    other.refresh_from_db()
    assert other.status == Locker.Status.OCCUPIED
    assert other.passcode == '123456'


@pytest.mark.django_db
def test_system_reset_project_scope_resets_only_project_lockers(client, project, building, line_user):
    project_locker = _create_dirty_locker('lck-001', building, local_id='1')
    other_project = Project.objects.create(id='prj-002', name='Other Project', address='456 Test St')
    other_building = Building.objects.create(id='bld-002', project=other_project, name='Other Building')
    other_locker = _create_dirty_locker('lck-002', other_building, local_id='2')

    response = client.post(
        '/api/system/reset/',
        data={'scope': 'PROJECT', 'project_id': project.id},
        content_type='application/json',
        **_auth(line_user, client),
    )

    assert response.status_code == 200
    assert response.data['scope'] == 'PROJECT'
    assert response.data['reset_count'] == 1
    assert response.data['locker_ids'] == [project_locker.id]
    _assert_reset(project_locker)

    other_locker.refresh_from_db()
    assert other_locker.status == Locker.Status.OCCUPIED
    assert other_locker.passcode == '123456'


@pytest.mark.django_db
def test_system_reset_all_scope_resets_all_lockers(client, project, building, line_user):
    first = _create_dirty_locker('lck-001', building, local_id='1')
    other_building = Building.objects.create(id='bld-002', project=project, name='Building B')
    second = _create_dirty_locker('lck-002', other_building, local_id='2')

    response = client.post(
        '/api/system/reset/',
        data={'scope': 'ALL'},
        content_type='application/json',
        **_auth(line_user, client),
    )

    assert response.status_code == 200
    assert response.data['scope'] == 'ALL'
    assert response.data['reset_count'] == 2
    assert set(response.data['locker_ids']) == {first.id, second.id}
    _assert_reset(first)
    _assert_reset(second)


@pytest.mark.django_db
def test_system_reset_rejects_invalid_scope(client, line_user):
    response = client.post(
        '/api/system/reset/',
        data={'scope': 'ROOM'},
        content_type='application/json',
        **_auth(line_user, client),
    )

    assert response.status_code == 400
    assert 'scope must be one of' in response.data['error']


@pytest.mark.django_db
def test_system_reset_requires_project_id_for_project_scope(client, line_user):
    response = client.post(
        '/api/system/reset/',
        data={'scope': 'PROJECT'},
        content_type='application/json',
        **_auth(line_user, client),
    )

    assert response.status_code == 400
    assert response.data['error'] == 'project_id is required for PROJECT scope.'
