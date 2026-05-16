from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Building, Locker
from .realtime import locker_group_name
from .serializers import LockerSerializer


class LockerConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.building_id = self.scope['url_route']['kwargs']['building_id']
        self.group_name = locker_group_name(self.building_id)

        if not await self._building_exists():
            await self.close(code=4404)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json(await self._snapshot_payload())

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        command = content.get('command')

        if command == 'ping':
            await self.send_json({'type': 'pong'})
            return

        if command == 'snapshot':
            await self.send_json(await self._snapshot_payload())
            return

        await self.send_json({
            'type': 'error',
            'error': "Unsupported command. Use 'ping' or 'snapshot'.",
        })

    async def locker_update(self, event):
        await self.send_json(event['payload'])

    @database_sync_to_async
    def _building_exists(self):
        return Building.objects.filter(id=self.building_id).exists()

    @database_sync_to_async
    def _snapshot_payload(self):
        lockers = Locker.objects.filter(building_id=self.building_id).order_by('local_id', 'id')
        return {
            'type': 'locker.snapshot',
            'building_id': self.building_id,
            'lockers': LockerSerializer(lockers, many=True).data,
        }
