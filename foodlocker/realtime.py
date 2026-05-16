import logging
import re
from collections import defaultdict

from asgiref.sync import async_to_sync
from django.conf import settings

from .serializers import LockerSerializer

logger = logging.getLogger(__name__)

_GROUP_SAFE_RE = re.compile(r"[^a-zA-Z0-9_.-]")


def locker_group_name(building_id):
    safe_building_id = _GROUP_SAFE_RE.sub("_", str(building_id or "unknown"))[:80]
    return f"lockers.{safe_building_id}"


def locker_payload(locker):
    return LockerSerializer(locker).data


def broadcast_locker_update(locker, *, event_type="locker.updated", action=None):
    return _broadcast(
        locker_group_name(locker.building_id),
        {
            "type": "locker.update",
            "event": event_type,
            "action": action,
            "locker_id": locker.id,
            "locker": locker_payload(locker),
        },
    )


def broadcast_bulk_locker_update(affected_lockers, *, event_type="lockers.updated", action=None, metadata=None):
    locker_ids_by_building = defaultdict(list)
    for locker in affected_lockers:
        locker_ids_by_building[locker["building_id"]].append(locker["id"])

    sent = 0
    for building_id, locker_ids in locker_ids_by_building.items():
        if _broadcast(
            locker_group_name(building_id),
            {
                "type": "lockers.bulk_update",
                "event": event_type,
                "action": action,
                "locker_ids": locker_ids,
                "building_id": building_id,
                "metadata": metadata or {},
            },
        ):
            sent += 1
    return sent


def _broadcast(group_name, message):
    if not getattr(settings, "LOCKER_WEBSOCKET_BROADCAST_ENABLED", True):
        return False

    try:
        from channels.layers import get_channel_layer
    except ModuleNotFoundError as exc:
        if exc.name != "channels":
            raise
        return False

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return False

    try:
        async_to_sync(channel_layer.group_send)(group_name, message)
    except Exception:
        logger.debug("Locker websocket broadcast failed", exc_info=True)
        return False

    return True
