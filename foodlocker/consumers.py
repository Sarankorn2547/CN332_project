from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Locker
from .realtime import locker_group_name
from .serializers import LockerSerializer


class LockerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.building_id = self.scope["url_route"]["kwargs"]["building_id"]
        self.group_name = locker_group_name(self.building_id)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(await self._snapshot("lockers.initial_state"))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        command = content.get("command") or content.get("type")
        if command in {"refresh", "list"}:
            await self.send_json(await self._snapshot("lockers.snapshot"))
            return
        if command == "ping":
            await self.send_json({"type": "pong"})
            return

        await self.send_json({
            "type": "error",
            "error": "Unsupported command. Use refresh, list, or ping.",
        })

    async def locker_update(self, event):
        await self.send_json({
            "type": event.get("event", "locker.updated"),
            "action": event.get("action"),
            "locker_id": event.get("locker_id"),
            "locker": event.get("locker"),
        })

    async def lockers_bulk_update(self, event):
        await self.send_json({
            "type": event.get("event", "lockers.updated"),
            "action": event.get("action"),
            "building_id": event.get("building_id"),
            "locker_ids": event.get("locker_ids", []),
            "metadata": event.get("metadata", {}),
        })

    @database_sync_to_async
    def _snapshot(self, event_type):
        lockers = Locker.objects.filter(
            building_id=self.building_id,
        ).order_by("local_id", "id")
        return {
            "type": event_type,
            "building_id": self.building_id,
            "count": lockers.count(),
            "lockers": LockerSerializer(lockers, many=True).data,
        }
