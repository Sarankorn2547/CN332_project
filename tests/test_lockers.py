import pytest
from django.urls import reverse
from foodlocker.models import LockerLog


def _get_token(client, line_user):
    resp = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    return resp.data['access']


# ─── List ───────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_list_lockers(client, locker):
    response = client.get('/api/lockers/')
    assert response.status_code == 200
    ids = [l['id'] for l in response.data]
    assert locker.id in ids


@pytest.mark.django_db
def test_list_lockers_filter_by_building(client, locker, building):
    response = client.get(f'/api/lockers/?building_id={building.id}')
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == locker.id


@pytest.mark.django_db
def test_list_lockers_filter_unknown_building(client, locker):
    response = client.get('/api/lockers/?building_id=GHOST-BLD')
    assert response.status_code == 200
    assert response.data == []


# ─── Retrieve ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_retrieve_locker(client, locker):
    response = client.get(f'/api/lockers/{locker.id}/')
    assert response.status_code == 200
    assert response.data['id'] == locker.id
    assert response.data['size'] == locker.size
    assert response.data['status'] == 'AVAILABLE'


@pytest.mark.django_db
def test_retrieve_locker_not_found(client):
    response = client.get('/api/lockers/GHOST-LCK/')
    assert response.status_code == 404


# ─── Update (PUT) ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_update_locker_unauthenticated(client, locker):
    payload = {
        'local_id': locker.local_id,
        'size': 'L',
        'status': 'AVAILABLE',
        'type': locker.type,
        'is_door_open': False,
        'has_object': False,
        'is_locked': True,
    }
    response = client.put(
        f'/api/lockers/{locker.id}/',
        data=payload,
        content_type='application/json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_update_locker_authenticated(client, locker, line_user):
    token = _get_token(client, line_user)
    payload = {
        'local_id': locker.local_id,
        'size': 'L',
        'status': 'AVAILABLE',
        'type': locker.type,
        'is_door_open': False,
        'has_object': False,
        'is_locked': True,
    }
    response = client.put(
        f'/api/lockers/{locker.id}/',
        data=payload,
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['size'] == 'L'


@pytest.mark.django_db
def test_update_locker_partial(client, locker, line_user):
    token = _get_token(client, line_user)
    response = client.patch(
        f'/api/lockers/{locker.id}/',
        data={'size': 'S'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['size'] == 'S'


@pytest.mark.django_db
def test_update_locker_not_found(client, line_user):
    token = _get_token(client, line_user)
    payload = {
        'local_id': '99',
        'size': 'M',
        'status': 'AVAILABLE',
        'type': 'FOOD',
        'is_door_open': False,
        'has_object': False,
        'is_locked': True,
    }
    response = client.put(
        '/api/lockers/GHOST-LCK/',
        data=payload,
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_locker_building_readonly(client, locker, line_user, project):
    """building field in PUT body is silently ignored — locker stays in original building."""
    from foodlocker.models import Building
    other = Building.objects.create(id='bld-other', project=project, name='Other Building')
    token = _get_token(client, line_user)
    payload = {
        'local_id': locker.local_id,
        'size': locker.size,
        'status': locker.status,
        'type': locker.type,
        'is_door_open': locker.is_door_open,
        'has_object': locker.has_object,
        'is_locked': locker.is_locked,
        'building': other.id,
    }
    response = client.put(
        f'/api/lockers/{locker.id}/',
        data=payload,
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    locker.refresh_from_db()
    assert locker.building_id != other.id


@pytest.mark.django_db
def test_update_locker_id_readonly(client, locker, line_user):
    """id in PUT body is silently ignored — locker keeps its original id."""
    token = _get_token(client, line_user)
    payload = {
        'id': 'new-id-attempt',
        'local_id': locker.local_id,
        'size': locker.size,
        'status': locker.status,
        'type': locker.type,
        'is_door_open': locker.is_door_open,
        'has_object': locker.has_object,
        'is_locked': locker.is_locked,
    }
    response = client.put(
        f'/api/lockers/{locker.id}/',
        data=payload,
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['id'] == locker.id


@pytest.mark.django_db
def test_update_locker_valid_status_choices(client, locker, line_user):
    token = _get_token(client, line_user)
    for new_status in ('BOOKED', 'OCCUPIED', 'AVAILABLE'):
        response = client.patch(
            f'/api/lockers/{locker.id}/',
            data={'status': new_status},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )
        assert response.status_code == 200
        assert response.data['status'] == new_status


# ─── Locker Workflow Actions ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_book_locker_success(client, locker, line_user):
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/book/',
        data={'building_id': locker.building_id, 'size': locker.size, 'type': locker.type},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert 'locker_id' in response.data
    assert 'qr_data' in response.data
    assert 'passcode' in response.data


@pytest.mark.django_db
def test_book_locker_logs_actor_id(client, locker, line_user):
    """After booking, LockerLog must record the authenticated user's line_user_id as actor_id."""
    token = _get_token(client, line_user)
    client.post(
        '/api/lockers/book/',
        data={'building_id': locker.building_id, 'size': locker.size, 'type': locker.type},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    log = LockerLog.objects.filter(action='ACTION_BOOK').first()
    assert log is not None
    assert log.actor_id == line_user.line_user_id


@pytest.mark.django_db
def test_book_locker_no_available(client, locker, line_user):
    locker.status = 'BOOKED'
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/book/',
        data={'building_id': locker.building_id, 'size': locker.size, 'type': locker.type},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_book_locker_missing_fields(client, line_user):
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/book/',
        data={'building_id': 'bld-001'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_book_locker_unauthenticated(client, locker):
    response = client.post(
        '/api/lockers/book/',
        data={'building_id': locker.building_id, 'size': locker.size, 'type': locker.type},
        content_type='application/json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_open_locker_success(client, locker, line_user):
    locker.status = 'BOOKED'
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        f'/api/lockers/{locker.id}/open/',
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['is_door_open'] is True


@pytest.mark.django_db
def test_open_locker_not_found(client, line_user):
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/GHOST-LCK/open/',
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_deposit_success(client, locker, line_user):
    locker.status = 'BOOKED'
    locker.is_door_open = True
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        f'/api/lockers/{locker.id}/deposit/',
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['status'] == 'OCCUPIED'
    assert response.data['has_object'] is True


@pytest.mark.django_db
def test_deposit_door_not_open(client, locker, line_user):
    locker.status = 'BOOKED'
    locker.is_door_open = False
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        f'/api/lockers/{locker.id}/deposit/',
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_verify_qr_with_qr_data(client, locker, line_user):
    locker.status = 'OCCUPIED'
    locker.qr_data = 'test-qr-abc'
    locker.passcode = '000000'
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/verify-qr/',
        data={'qr_data': 'test-qr-abc'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['is_door_open'] is True


@pytest.mark.django_db
def test_verify_qr_with_passcode(client, locker, line_user):
    locker.status = 'OCCUPIED'
    locker.qr_data = 'test-qr-xyz'
    locker.passcode = '123456'
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/verify-qr/',
        data={'passcode': '123456'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['is_door_open'] is True


@pytest.mark.django_db
def test_verify_qr_invalid(client, locker, line_user):
    locker.status = 'OCCUPIED'
    locker.qr_data = 'correct-qr'
    locker.passcode = '999999'
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        '/api/lockers/verify-qr/',
        data={'qr_data': 'wrong-qr'},
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_pickup_success(client, locker, line_user):
    locker.status = 'OCCUPIED'
    locker.has_object = True
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        f'/api/lockers/{locker.id}/pickup/',
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 200
    assert response.data['status'] == 'AVAILABLE'
    assert response.data['has_object'] is False


@pytest.mark.django_db
def test_pickup_wrong_status(client, locker, line_user):
    locker.status = 'BOOKED'
    locker.save()
    token = _get_token(client, line_user)
    response = client.post(
        f'/api/lockers/{locker.id}/pickup/',
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {token}',
    )
    assert response.status_code == 400
