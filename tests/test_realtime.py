import pytest
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.test import override_settings
from django.urls import reverse

from config.asgi import application
from foodlocker.models import Locker


IN_MEMORY_CHANNEL_LAYER = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


def _get_token(client, line_user):
    resp = client.post(
        reverse('token-obtain'),
        data={'line_user_id': line_user.line_user_id},
        content_type='application/json',
    )
    return resp.data['access']


def _auth(client, line_user):
    return {'HTTP_AUTHORIZATION': f'Bearer {_get_token(client, line_user)}'}


async def _connect(path):
    communicator = WebsocketCommunicator(application, path)
    connected, _ = await communicator.connect()
    assert connected is True
    return communicator


async def _receive(communicator):
    return await communicator.receive_json_from(timeout=1)


async def _disconnect(communicator):
    await communicator.disconnect()


@database_sync_to_async
def _post(client, path, data, auth):
    return client.post(
        path,
        data=data,
        content_type='application/json',
        **auth,
    )


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER)
def test_locker_websocket_sends_building_snapshot(building, locker):
    async_to_sync(_assert_locker_websocket_sends_building_snapshot)(building.id, locker.id)


async def _assert_locker_websocket_sends_building_snapshot(building_id, locker_id):
    communicator = await _connect(f'/ws/lockers/{building_id}/')

    snapshot = await _receive(communicator)

    assert snapshot['type'] == 'locker.snapshot'
    assert snapshot['building_id'] == building_id
    assert [item['id'] for item in snapshot['lockers']] == [locker_id]

    await _disconnect(communicator)


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER)
def test_locker_websocket_broadcasts_full_locker_workflow(client, building, locker, line_user):
    auth = _auth(client, line_user)
    async_to_sync(_assert_locker_websocket_broadcasts_full_locker_workflow)(
        client,
        building.id,
        locker.size,
        locker.type,
        line_user.line_user_id,
        auth,
    )


async def _assert_locker_websocket_broadcasts_full_locker_workflow(
    client,
    building_id,
    locker_size,
    locker_type,
    line_user_id,
    auth,
):
    communicator = await _connect(f'/ws/lockers/{building_id}/')
    await _receive(communicator)

    book_response = await _post(
        client,
        '/api/lockers/book/',
        {'building_id': building_id, 'size': locker_size, 'type': locker_type},
        auth,
    )
    assert book_response.status_code == 200
    event = await _receive(communicator)
    assert event['type'] == 'locker.updated'
    assert event['action'] == 'ACTION_BOOK'
    assert event['actor_id'] == line_user_id
    assert event['locker']['status'] == Locker.Status.BOOKED

    locker_id = book_response.data['locker_id']
    open_response = await _post(
        client,
        f'/api/lockers/{locker_id}/open/',
        {},
        auth,
    )
    assert open_response.status_code == 200
    event = await _receive(communicator)
    assert event['action'] == 'ACTION_OPEN'
    assert event['locker']['is_door_open'] is True
    assert event['locker']['is_locked'] is False

    deposit_response = await _post(
        client,
        f'/api/lockers/{locker_id}/deposit/',
        {},
        auth,
    )
    assert deposit_response.status_code == 200
    event = await _receive(communicator)
    assert event['action'] == 'ACTION_DEPOSIT'
    assert event['locker']['status'] == Locker.Status.OCCUPIED
    assert event['locker']['has_object'] is True

    verify_response = await _post(
        client,
        '/api/lockers/verify-qr/',
        {'passcode': book_response.data['passcode']},
        auth,
    )
    assert verify_response.status_code == 200
    event = await _receive(communicator)
    assert event['action'] == 'ACTION_VERIFY_QR'
    assert event['locker']['is_door_open'] is True
    assert event['metadata'] == {'method': 'passcode'}

    pickup_response = await _post(
        client,
        f'/api/lockers/{locker_id}/pickup/',
        {},
        auth,
    )
    assert pickup_response.status_code == 200
    event = await _receive(communicator)
    assert event['action'] == 'ACTION_PICKUP'
    assert event['locker']['status'] == Locker.Status.AVAILABLE
    assert event['locker']['has_object'] is False

    await _disconnect(communicator)


@pytest.mark.django_db(transaction=True)
@override_settings(CHANNEL_LAYERS=IN_MEMORY_CHANNEL_LAYER)
def test_locker_websocket_rejects_unknown_building():
    async_to_sync(_assert_locker_websocket_rejects_unknown_building)()


async def _assert_locker_websocket_rejects_unknown_building():
    communicator = WebsocketCommunicator(application, '/ws/lockers/ghost-building/')
    connected, _ = await communicator.connect()
    assert connected is False
