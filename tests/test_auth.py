import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_obtain_token_success(client, line_user):
    response = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data


@pytest.mark.django_db
def test_obtain_token_user_not_found(client):
    response = client.post(
        reverse('token-obtain'),
        data={'line_user_id': 'GHOST_USER'},
        content_type='application/json',
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_obtain_token_missing_line_user_id(client):
    response = client.post(reverse('token-obtain'), data={}, content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_protected_endpoint_without_token(client, building):
    payload = {'building_id': building.id, 'size': 'M', 'type': 'FOOD'}
    response = client.post(
        '/api/lockers/book/',
        data=payload,
        content_type='application/json',
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_protected_endpoint_with_valid_token(client, line_user, building):
    token_response = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    access = token_response.data['access']
    payload = {'building_id': building.id, 'size': 'M', 'type': 'FOOD'}
    response = client.post(
        '/api/lockers/book/',
        data=payload,
        content_type='application/json',
        HTTP_AUTHORIZATION=f'Bearer {access}',
    )
    # Auth passes — may get 400 (no matching locker) but not 401/403
    assert response.status_code != 401
    assert response.status_code != 403


@pytest.mark.django_db
def test_refresh_token(client, line_user):
    token_response = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    refresh = token_response.data['refresh']
    response = client.post(
        reverse('token-refresh'),
        data={'refresh': refresh},
        content_type='application/json',
    )
    assert response.status_code == 200
    assert 'access' in response.data
