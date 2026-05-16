from foodlocker.models import Locker, LockerLog


def test_backend_b_query_indexes_are_declared():
    locker_indexes = {index.name for index in Locker._meta.indexes}
    log_indexes = {index.name for index in LockerLog._meta.indexes}

    assert {
        "locker_bldg_status_idx",
        "locker_type_status_idx",
        "locker_deposit_idx",
        "locker_qr_idx",
        "locker_pin_idx",
    }.issubset(locker_indexes)

    assert {
        "llog_locker_action_idx",
        "llog_actor_idx",
        "llog_created_idx",
    }.issubset(log_indexes)
