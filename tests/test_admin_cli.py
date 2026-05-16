import pytest
from django.urls import reverse

from foodlocker.models import Locker, LockerLog


def _get_token(client, line_user):
    resp = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    return resp.data['access']


def _auth(client, line_user):
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


@pytest.mark.django_db
def test_admin_cli_requires_authentication(client):
    response = client.post(
        reverse('admin-cli'),
        data={'command': 'list'},
        content_type='application/json',
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_admin_cli_requires_command(client, line_user):
    response = client.post(
        reverse('admin-cli'),
        data={},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 400
    assert response.data['error'] == 'command is required'


@pytest.mark.django_db
def test_admin_cli_list_lockers(client, locker, line_user):
    response = client.post(
        reverse('admin-cli'),
        data={'command': 'list --status=available --type=food'},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 200
    assert response.data['command'] == 'list'
    assert response.data['count'] == 1
    assert response.data['lockers'][0]['id'] == locker.id


@pytest.mark.django_db
def test_admin_cli_open_locker(client, locker, line_user):
    locker.status = Locker.Status.BOOKED
    locker.passcode = '123456'
    locker.qr_data = 'qr-token'
    locker.is_door_open = False
    locker.is_locked = True
    locker.save()

    response = client.post(
        reverse('admin-cli'),
        data={'command': f'open {locker.id}'},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 200
    assert response.data['command'] == 'open'
    assert response.data['locker']['id'] == locker.id

    locker.refresh_from_db()
    assert locker.is_door_open is True
    assert locker.is_locked is False
    assert LockerLog.objects.filter(
        locker=locker,
        action='ACTION_OPEN',
        actor_id=line_user.line_user_id,
    ).exists()


@pytest.mark.django_db
def test_admin_cli_open_locker_requires_id(client, line_user):
    response = client.post(
        reverse('admin-cli'),
        data={'command': 'open'},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 400
    assert response.data['error'] == 'Usage: open <locker_id>'


@pytest.mark.django_db
def test_admin_cli_reset_locker(client, locker, line_user):
    _dirty_locker(locker)

    response = client.post(
        reverse('admin-cli'),
        data={'command': f'reset {locker.id}'},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 200
    assert response.data['command'] == 'reset'
    assert response.data['scope'] == 'LOCKER'
    assert response.data['reset_count'] == 1
    assert response.data['locker_ids'] == [locker.id]

    locker.refresh_from_db()
    assert locker.status == Locker.Status.AVAILABLE
    assert locker.passcode == ''
    assert locker.qr_data == ''
    assert locker.has_object is False


@pytest.mark.django_db
def test_admin_cli_reset_building(client, locker, line_user, building):
    _dirty_locker(locker)

    response = client.post(
        reverse('admin-cli'),
        data={'command': f'reset --building={building.id}'},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 200
    assert response.data['scope'] == 'BUILDING'
    assert response.data['reset_count'] == 1


@pytest.mark.django_db
def test_admin_cli_unknown_command(client, line_user):
    response = client.post(
        reverse('admin-cli'),
        data={'command': 'reboot'},
        content_type='application/json',
        **_auth(client, line_user),
    )

    assert response.status_code == 400
    assert "Unknown command 'reboot'" in response.data['error']
