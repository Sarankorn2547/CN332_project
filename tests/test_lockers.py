import pytest
from django.urls import reverse


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
