import pytest

from foodlocker.models import Locker, LockerLog
from foodlocker.services import LockerService
from foodlocker.tasks import check_abandoned_food_lockers


def _occupy(locker, *, deposit_start_time, locker_type="FOOD"):
    locker.type = locker_type
    locker.status = Locker.Status.OCCUPIED
    locker.has_object = True
    locker.is_locked = True
    locker.is_door_open = False
    locker.passcode = "123456"
    locker.qr_data = "qr-token"
    locker.deposit_start_time = deposit_start_time
    locker.save()
    return locker


@pytest.mark.django_db
def test_abandoned_food_check_flags_overdue_food_locker(locker, settings):
    settings.LOCKER_WEBSOCKET_BROADCAST_ENABLED = False
    now = 1_710_000_000
    _occupy(locker, deposit_start_time=now - (25 * 60 * 60))

    result = LockerService.check_abandoned_food_lockers(now=now)

    assert result["matched_count"] == 1
    assert result["abandoned_count"] == 1
    assert result["locker_ids"] == [locker.id]

    log = LockerLog.objects.get(locker=locker, action="ACTION_ABANDONED")
    assert log.actor_id == "celery"
    assert log.metadata["deposit_start_time"] == locker.deposit_start_time
    assert log.metadata["requires_staff_intervention"] is True

    locker.refresh_from_db()
    assert locker.status == Locker.Status.OCCUPIED
    assert locker.has_object is True


@pytest.mark.django_db
def test_abandoned_food_check_ignores_fresh_and_non_food_lockers(locker, building, settings):
    settings.LOCKER_WEBSOCKET_BROADCAST_ENABLED = False
    now = 1_710_000_000
    _occupy(locker, deposit_start_time=now - (2 * 60 * 60))
    asset_locker = Locker.objects.create(
        id="lck-asset",
        building=building,
        local_id="2",
        size="M",
        status=Locker.Status.AVAILABLE,
        type="ASSET",
        passcode="",
        qr_data="",
        is_door_open=False,
        has_object=False,
        is_locked=True,
    )
    _occupy(asset_locker, deposit_start_time=now - (25 * 60 * 60), locker_type="ASSET")

    result = LockerService.check_abandoned_food_lockers(now=now)

    assert result["matched_count"] == 0
    assert result["abandoned_count"] == 0
    assert LockerLog.objects.filter(action="ACTION_ABANDONED").count() == 0


@pytest.mark.django_db
def test_abandoned_food_check_is_idempotent_for_same_deposit(locker, settings):
    settings.LOCKER_WEBSOCKET_BROADCAST_ENABLED = False
    now = 1_710_000_000
    _occupy(locker, deposit_start_time=now - (25 * 60 * 60))

    first = LockerService.check_abandoned_food_lockers(now=now)
    second = LockerService.check_abandoned_food_lockers(now=now)

    assert first["abandoned_count"] == 1
    assert second["matched_count"] == 1
    assert second["abandoned_count"] == 0
    assert LockerLog.objects.filter(locker=locker, action="ACTION_ABANDONED").count() == 1


@pytest.mark.django_db
def test_abandoned_food_celery_task_delegates_to_service(locker, settings):
    settings.LOCKER_WEBSOCKET_BROADCAST_ENABLED = False
    now = 1_710_000_000
    _occupy(locker, deposit_start_time=now - (25 * 60 * 60))

    result = check_abandoned_food_lockers(now=now)

    assert result["abandoned_count"] == 1
    assert result["locker_ids"] == [locker.id]
