import time

import pytest

from foodlocker.models import Locker, LockerLog
from foodlocker.tasks import check_abandoned_food_lockers


def _locker(building, locker_id, *, locker_type="FOOD", age_seconds=25 * 60 * 60):
    return Locker.objects.create(
        id=locker_id,
        building=building,
        local_id=locker_id,
        size="M",
        status=Locker.Status.OCCUPIED,
        type=locker_type,
        passcode="123456",
        qr_data=f"qr-{locker_id}",
        is_door_open=False,
        has_object=True,
        is_locked=True,
        deposit_start_time=int(time.time()) - age_seconds,
    )


@pytest.mark.django_db
def test_check_abandoned_food_lockers_resets_old_food_lockers(building):
    old_food = _locker(building, "old-food")
    recent_food = _locker(building, "recent-food", age_seconds=60)
    old_asset = _locker(building, "old-asset", locker_type="ASSET")

    result = check_abandoned_food_lockers.run()

    assert result["abandoned_count"] == 1
    assert result["locker_ids"] == [old_food.id]

    old_food.refresh_from_db()
    assert old_food.status == Locker.Status.AVAILABLE
    assert old_food.passcode == ""
    assert old_food.qr_data == ""
    assert old_food.has_object is False
    assert old_food.is_locked is True
    assert old_food.deposit_start_time is None

    recent_food.refresh_from_db()
    old_asset.refresh_from_db()
    assert recent_food.status == Locker.Status.OCCUPIED
    assert old_asset.status == Locker.Status.OCCUPIED

    log = LockerLog.objects.get(locker=old_food, action="ACTION_ABANDONED_TIMEOUT")
    assert log.actor_id == "celery"
    assert log.metadata["reason"] == "ABANDONED_FOOD_TIMEOUT"
