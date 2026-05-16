import hashlib

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from .serializers import LockerSerializer


def locker_group_name(building_id: str) -> str:
    digest = hashlib.sha1(str(building_id).encode('utf-8')).hexdigest()
    return f'lockers_{digest}'


def locker_payload(locker, action: str, actor_id: str = 'system', metadata=None) -> dict:
    return {
        'type': 'locker.updated',
        'action': action,
        'building_id': locker.building_id,
        'actor_id': actor_id,
        'locker': LockerSerializer(locker).data,
        'metadata': metadata or {},
    }


def broadcast_locker_update(locker, action: str, actor_id: str = 'system', metadata=None) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = locker_payload(locker, action=action, actor_id=actor_id, metadata=metadata)

    def send_update():
        async_to_sync(channel_layer.group_send)(
            locker_group_name(locker.building_id),
            {
                'type': 'locker.update',
                'payload': payload,
            },
        )

    transaction.on_commit(send_update)
