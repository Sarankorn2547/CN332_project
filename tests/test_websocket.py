import pytest
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from foodlocker.realtime import locker_group_name


@pytest.mark.django_db(transaction=True)
def test_locker_websocket_sends_initial_state_and_updates(locker, settings):
    settings.CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

    from config.asgi import application

    async def scenario():
        communicator = WebsocketCommunicator(
            application,
            f"/ws/lockers/{locker.building_id}/",
        )
        connected, _ = await communicator.connect()
        assert connected is True

        initial = await communicator.receive_json_from(timeout=1)
        assert initial["type"] == "lockers.initial_state"
        assert initial["building_id"] == locker.building_id
        assert initial["count"] == 1
        assert initial["lockers"][0]["id"] == locker.id

        await get_channel_layer().group_send(
            locker_group_name(locker.building_id),
            {
                "type": "locker.update",
                "event": "locker.booked",
                "action": "ACTION_BOOK",
                "locker_id": locker.id,
                "locker": {"id": locker.id, "status": "BOOKED"},
            },
        )
        update = await communicator.receive_json_from(timeout=1)
        assert update["type"] == "locker.booked"
        assert update["action"] == "ACTION_BOOK"
        assert update["locker_id"] == locker.id
        assert update["locker"]["status"] == "BOOKED"

        await communicator.disconnect()

    async_to_sync(scenario)()
