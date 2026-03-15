import uuid
import random
import time
from .models import Locker, LockerLog

class LockerService:
    @staticmethod
    def book_locker(building_id: str, size: str, locker_type: str) -> Locker:
        locker = Locker.objects.filter(
            building_id=building_id,
            size=size,
            type=locker_type,
            status="AVAILABLE"
        ).first()

        if not locker:
            raise ValueError(f"No available locker found for size '{size}' and type '{locker_type}' in building '{building_id}'.")

        passcode = f"{random.randint(0, 999999):06d}"
        qr_data = str(uuid.uuid4())

        locker.status = "BOOKED"
        locker.passcode = passcode
        locker.qr_data = qr_data
        locker.is_locked = True
        locker.is_door_open = False
        locker.save()

        LockerLog.objects.create(
            locker=locker,
            action="ACTION_BOOK",
            actor_id="system",
            metadata={"size": size, "type": locker_type}
        )

        return locker

    @staticmethod
    def open_locker(locker_id: str, actor_id: str = "system") -> Locker:
        try:
            locker = Locker.objects.get(id=locker_id)
        except Locker.DoesNotExist:
            raise ValueError(f"Locker with id '{locker_id}' not found.")

        if locker.status not in ["BOOKED", "OCCUPIED"]:
            raise ValueError(f"Locker '{locker_id}' cannot be opened in status '{locker.status}'.")

        locker.is_door_open = True
        locker.is_locked = False
        locker.save()

        LockerLog.objects.create(
            locker=locker,
            action="ACTION_OPEN",
            actor_id=actor_id
        )

        return locker

    @staticmethod
    def confirm_deposit(locker_id: str, actor_id: str = "system") -> Locker:
        try:
            locker = Locker.objects.get(id=locker_id)
        except Locker.DoesNotExist:
            raise ValueError(f"Locker with id '{locker_id}' not found.")

        if locker.status != "BOOKED":
            raise ValueError(f"Locker '{locker_id}' must be in BOOKED status to confirm deposit.")

        if not locker.is_door_open:
            raise ValueError(f"Locker '{locker_id}' door must be open to deposit.")

        locker.status = "OCCUPIED"
        locker.has_object = True
        locker.is_door_open = False
        locker.is_locked = True
        locker.deposit_start_time = int(time.time())
        locker.save()

        LockerLog.objects.create(
            locker=locker,
            action="ACTION_DEPOSIT",
            actor_id=actor_id
        )

        return locker
