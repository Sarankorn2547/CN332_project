import uuid
import random
import time
from django.db import models, transaction
from .models import Locker, LockerLog

class LockerService:
    RESET_SCOPES = {"LOCKER", "BUILDING", "PROJECT", "ALL"}

    @staticmethod
    def book_locker(building_id: str, size: str, locker_type: str, actor_id: str = "system") -> Locker:
        with transaction.atomic():
            locker = Locker.objects.select_for_update().filter(
                building_id=building_id,
                size=size,
                type=locker_type,
                status=Locker.Status.AVAILABLE
            ).order_by("id").first()

            if not locker:
                raise ValueError(f"No available locker found for size '{size}' and type '{locker_type}' in building '{building_id}'.")

            passcode = f"{random.randint(0, 999999):06d}"
            qr_data = str(uuid.uuid4())

            locker.status = Locker.Status.BOOKED
            locker.passcode = passcode
            locker.qr_data = qr_data
            locker.is_locked = True
            locker.is_door_open = False
            locker.save(update_fields=["status", "passcode", "qr_data", "is_locked", "is_door_open"])

            LockerLog.objects.create(
                locker=locker,
                action="ACTION_BOOK",
                actor_id=actor_id,
                metadata={"size": size, "type": locker_type}
            )

        return locker

    @staticmethod
    def open_locker(locker_id: str, actor_id: str = "system") -> Locker:
        try:
            locker = Locker.objects.get(id=locker_id)
        except Locker.DoesNotExist:
            raise ValueError(f"Locker with id '{locker_id}' not found.")

        if locker.status not in [Locker.Status.BOOKED, Locker.Status.OCCUPIED]:
            raise ValueError(f"Locker '{locker_id}' cannot be opened in status '{locker.status}'.")

        locker.is_door_open = True
        locker.is_locked = False
        locker.save(update_fields=["is_door_open", "is_locked"])

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

        if locker.status != Locker.Status.BOOKED:
            raise ValueError(f"Locker '{locker_id}' must be in BOOKED status to confirm deposit.")

        if not locker.is_door_open:
            raise ValueError(f"Locker '{locker_id}' door must be open to deposit.")

        locker.status = Locker.Status.OCCUPIED
        locker.has_object = True
        locker.is_door_open = False
        locker.is_locked = True
        locker.deposit_start_time = int(time.time())
        locker.save(update_fields=[
            "status",
            "has_object",
            "is_door_open",
            "is_locked",
            "deposit_start_time",
        ])

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
            status=Locker.Status.OCCUPIED
        ).filter(
            models.Q(qr_data=qr_data) | models.Q(passcode=passcode) if qr_data and passcode else
            models.Q(qr_data=qr_data) if qr_data else
            models.Q(passcode=passcode)
        ).first()

        if not locker:
            raise ValueError("Invalid QR code or Passcode, or locker is not occupied.")

        locker.is_door_open = True
        locker.is_locked = False
        locker.save(update_fields=["is_door_open", "is_locked"])

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

        if locker.status != Locker.Status.OCCUPIED:
            raise ValueError(f"Locker '{locker_id}' must be OCCUPIED to pickup.")

        if locker.is_locked or not locker.is_door_open:
            raise ValueError(f"Locker '{locker_id}' must be unlocked before pickup.")

        locker.status = Locker.Status.AVAILABLE
        locker.passcode = ""
        locker.qr_data = ""
        locker.has_object = False
        locker.is_door_open = False
        locker.is_locked = True
        locker.deposit_start_time = None
        locker.save(update_fields=[
            "status",
            "passcode",
            "qr_data",
            "has_object",
            "is_door_open",
            "is_locked",
            "deposit_start_time",
        ])

        LockerLog.objects.create(
            locker=locker,
            action="ACTION_PICKUP",
            actor_id=actor_id
        )

        return locker

    @staticmethod
    def reset_lockers(
        scope: str,
        *,
        locker_id: str = None,
        building_id: str = None,
        project_id: str = None,
        actor_id: str = "system",
    ) -> dict:
        normalized_scope = (scope or "").upper()
        if normalized_scope not in LockerService.RESET_SCOPES:
            raise ValueError("scope must be one of LOCKER, BUILDING, PROJECT, or ALL.")

        queryset = Locker.objects.all()
        metadata = {"scope": normalized_scope}

        if normalized_scope == "LOCKER":
            if not locker_id:
                raise ValueError("locker_id is required for LOCKER scope.")
            queryset = queryset.filter(id=locker_id)
            metadata["locker_id"] = locker_id
        elif normalized_scope == "BUILDING":
            if not building_id:
                raise ValueError("building_id is required for BUILDING scope.")
            queryset = queryset.filter(building_id=building_id)
            metadata["building_id"] = building_id
        elif normalized_scope == "PROJECT":
            if not project_id:
                raise ValueError("project_id is required for PROJECT scope.")
            queryset = queryset.filter(building__project_id=project_id)
            metadata["project_id"] = project_id

        locker_ids = list(queryset.order_by("id").values_list("id", flat=True))
        if normalized_scope == "LOCKER" and not locker_ids:
            raise Locker.DoesNotExist(f"Locker with id '{locker_id}' not found.")

        reset_fields = {
            "status": Locker.Status.AVAILABLE,
            "passcode": "",
            "qr_data": "",
            "is_door_open": False,
            "has_object": False,
            "is_locked": True,
            "deposit_start_time": None,
        }

        with transaction.atomic():
            reset_count = queryset.update(**reset_fields)
            LockerLog.objects.bulk_create([
                LockerLog(
                    locker_id=target_id,
                    action="ACTION_RESET",
                    actor_id=actor_id,
                    metadata=metadata,
                )
                for target_id in locker_ids
            ])

        return {
            "scope": normalized_scope,
            "reset_count": reset_count,
            "locker_ids": locker_ids,
        }
