import uuid
import random
import time
from django.db import models
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

    @staticmethod
    def verify_qr(qr_data: str = None, passcode: str = None, actor_id: str = "customer") -> Locker:
        if not qr_data and not passcode:
            raise ValueError("Either qr_data or passcode must be provided.")

        locker = Locker.objects.filter(
            status="OCCUPIED"
        ).filter(
            models.Q(qr_data=qr_data) | models.Q(passcode=passcode) if qr_data and passcode else
            models.Q(qr_data=qr_data) if qr_data else
            models.Q(passcode=passcode)
        ).first()

        if not locker:
            raise ValueError("Invalid QR code or Passcode, or locker is not occupied.")

        locker.is_door_open = True
        locker.is_locked = False
        locker.save()

        LockerLog.objects.create(
            locker=locker,
            action="ACTION_VERIFY_QR",
            actor_id=actor_id,
            metadata={"method": "qr" if qr_data else "passcode"}
        )

        return locker

    @staticmethod
    def pickup_locker(locker_id: str, actor_id: str = "customer") -> Locker:
        try:
            locker = Locker.objects.get(id=locker_id)
        except Locker.DoesNotExist:
            raise ValueError(f"Locker with id '{locker_id}' not found.")

        if locker.status != "OCCUPIED":
            raise ValueError(f"Locker '{locker_id}' must be OCCUPIED to pickup.")

        locker.status = "AVAILABLE"
        locker.passcode = ""
        locker.qr_data = ""
        locker.has_object = False
        locker.is_door_open = False
        locker.is_locked = True
        locker.deposit_start_time = None
        locker.save()

        LockerLog.objects.create(
            locker=locker,
            action="ACTION_PICKUP",
            actor_id=actor_id
        )

        return locker
