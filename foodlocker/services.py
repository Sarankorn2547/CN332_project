import uuid
import random
import time
from django.db import models, transaction
from .models import Locker, LockerLog
from .realtime import broadcast_bulk_locker_update, broadcast_locker_update

class LockerService:
    RESET_SCOPES = {"LOCKER", "BUILDING", "PROJECT", "ALL"}

    @staticmethod
    def book_locker(building_id: str, size: str, locker_type: str) -> Locker:
        with transaction.atomic():
            locker = Locker.objects.select_for_update().filter(
                building_id=building_id,
                size=size,
                type=locker_type,
                status=Locker.Status.AVAILABLE
            ).first()

            if not locker:
                raise ValueError(f"No available locker found for size '{size}' and type '{locker_type}' in building '{building_id}'.")

            passcode = f"{random.randint(0, 999999):06d}"
            qr_data = str(uuid.uuid4())

            locker.status = Locker.Status.BOOKED
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
            transaction.on_commit(
                lambda: broadcast_locker_update(
                    locker,
                    event_type="locker.booked",
                    action="ACTION_BOOK",
                )
            )

        return locker

    @staticmethod
    def open_locker(locker_id: str, actor_id: str = "system") -> Locker:
        with transaction.atomic():
            try:
                locker = Locker.objects.select_for_update().get(id=locker_id)
            except Locker.DoesNotExist:
                raise ValueError(f"Locker with id '{locker_id}' not found.")

            if locker.status not in [Locker.Status.BOOKED, Locker.Status.OCCUPIED]:
                raise ValueError(f"Locker '{locker_id}' cannot be opened in status '{locker.status}'.")

            locker.is_door_open = True
            locker.is_locked = False
            locker.save()

            LockerLog.objects.create(
                locker=locker,
                action="ACTION_OPEN",
                actor_id=actor_id
            )
            transaction.on_commit(
                lambda: broadcast_locker_update(
                    locker,
                    event_type="locker.opened",
                    action="ACTION_OPEN",
                )
            )

        return locker

    @staticmethod
    def confirm_deposit(locker_id: str, actor_id: str = "system") -> Locker:
        with transaction.atomic():
            try:
                locker = Locker.objects.select_for_update().get(id=locker_id)
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
            locker.save()

            LockerLog.objects.create(
                locker=locker,
                action="ACTION_DEPOSIT",
                actor_id=actor_id
            )
            transaction.on_commit(
                lambda: broadcast_locker_update(
                    locker,
                    event_type="locker.occupied",
                    action="ACTION_DEPOSIT",
                )
            )

        return locker

    @staticmethod
    def verify_qr(qr_data: str = None, passcode: str = None, actor_id: str = "customer") -> Locker:
        if not qr_data and not passcode:
            raise ValueError("Either qr_data or passcode must be provided.")

        with transaction.atomic():
            locker = Locker.objects.select_for_update().filter(
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
            locker.save()

            LockerLog.objects.create(
                locker=locker,
                action="ACTION_VERIFY_QR",
                actor_id=actor_id,
                metadata={"method": "qr" if qr_data else "passcode"}
            )
            transaction.on_commit(
                lambda: broadcast_locker_update(
                    locker,
                    event_type="locker.verified",
                    action="ACTION_VERIFY_QR",
                )
            )

        return locker

    @staticmethod
    def pickup_locker(locker_id: str, actor_id: str = "customer") -> Locker:
        with transaction.atomic():
            try:
                locker = Locker.objects.select_for_update().get(id=locker_id)
            except Locker.DoesNotExist:
                raise ValueError(f"Locker with id '{locker_id}' not found.")

            if locker.status != Locker.Status.OCCUPIED:
                raise ValueError(f"Locker '{locker_id}' must be OCCUPIED to pickup.")

            locker.status = Locker.Status.AVAILABLE
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
            transaction.on_commit(
                lambda: broadcast_locker_update(
                    locker,
                    event_type="locker.available",
                    action="ACTION_PICKUP",
                )
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

        affected_lockers = list(queryset.values("id", "building_id"))
        locker_ids = [locker["id"] for locker in affected_lockers]
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
            transaction.on_commit(
                lambda: broadcast_bulk_locker_update(
                    affected_lockers,
                    event_type="lockers.reset",
                    action="ACTION_RESET",
                    metadata=metadata,
                )
            )

        return {
            "scope": normalized_scope,
            "reset_count": reset_count,
            "locker_ids": locker_ids,
        }

    @staticmethod
    def check_abandoned_food_lockers(
        threshold_seconds: int = 24 * 60 * 60,
        *,
        now: int = None,
        actor_id: str = "celery",
    ) -> dict:
        if threshold_seconds <= 0:
            raise ValueError("threshold_seconds must be greater than 0.")

        current_time = int(now if now is not None else time.time())
        cutoff_time = current_time - threshold_seconds
        queryset = Locker.objects.filter(
            type__iexact="FOOD",
            status=Locker.Status.OCCUPIED,
            has_object=True,
            deposit_start_time__isnull=False,
            deposit_start_time__lte=cutoff_time,
        ).order_by("building_id", "local_id", "id")

        flagged_lockers = []
        with transaction.atomic():
            lockers = list(queryset.select_for_update())
            for locker in lockers:
                already_flagged = LockerLog.objects.filter(
                    locker=locker,
                    action="ACTION_ABANDONED",
                    metadata__deposit_start_time=locker.deposit_start_time,
                ).exists()
                if already_flagged:
                    continue

                LockerLog.objects.create(
                    locker=locker,
                    action="ACTION_ABANDONED",
                    actor_id=actor_id,
                    metadata={
                        "deposit_start_time": locker.deposit_start_time,
                        "threshold_seconds": threshold_seconds,
                        "cutoff_time": cutoff_time,
                        "requires_staff_intervention": True,
                    },
                )
                flagged_lockers.append(locker)
                transaction.on_commit(
                    lambda locker=locker: broadcast_locker_update(
                        locker,
                        event_type="locker.abandoned",
                        action="ACTION_ABANDONED",
                    )
                )

        return {
            "matched_count": len(lockers),
            "abandoned_count": len(flagged_lockers),
            "locker_ids": [locker.id for locker in flagged_lockers],
            "threshold_seconds": threshold_seconds,
            "cutoff_time": cutoff_time,
        }
