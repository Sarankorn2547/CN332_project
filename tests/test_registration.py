import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_register_new_user(client, project, building):
    payload = {
        'line_user_id': 'U_NEW_001',
        'project_id': project.id,
        'building_id': building.id,
        'room_no': '202',
        'display_name': 'New User',
    }
    response = client.post(reverse('user-register'), data=payload, content_type='application/json')
    assert response.status_code == 201
    assert response.data['line_user_id'] == 'U_NEW_001'


@pytest.mark.django_db
def test_register_duplicate_line_user_id(client, line_user, project, building):
    payload = {
        'line_user_id': line_user.line_user_id,
        'project_id': project.id,
        'building_id': building.id,
        'room_no': '303',
        'display_name': 'Duplicate',
    }
    response = client.post(reverse('user-register'), data=payload, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_missing_fields(client):
    response = client.post(reverse('user-register'), data={}, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_invalid_project(client, building):
    payload = {
        'line_user_id': 'U_NEW_002',
        'project_id': 'nonexistent',
        'building_id': building.id,
        'room_no': '404',
        'display_name': 'Ghost',
    }
    response = client.post(reverse('user-register'), data=payload, content_type='application/json')
    assert response.status_code == 404


@pytest.mark.django_db
def test_user_status_no_active_locker(client, line_user):
    url = reverse('user-status') + f'?line_user_id={line_user.line_user_id}'
    response = client.get(url)
    assert response.status_code == 200
    assert response.data['status'] == 'NO_ACTIVE_LOCKER'


@pytest.mark.django_db
def test_user_status_not_found(client):
    url = reverse('user-status') + '?line_user_id=NONEXISTENT'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_user_status_missing_param(client):
    response = client.get(reverse('user-status'))
    assert response.status_code == 400
