import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from foodlocker.models import Locker, LockerLog


def _token(line_user):
    refresh = RefreshToken()
    refresh["line_user_id"] = line_user.line_user_id
    return str(refresh.access_token)


def _auth(line_user):
    return {"HTTP_AUTHORIZATION": f"Bearer {_token(line_user)}"}


def _create_locker(building, locker_id, *, local_id, status=Locker.Status.AVAILABLE, size="M", locker_type="FOOD"):
    return Locker.objects.create(
        id=locker_id,
        building=building,
        local_id=local_id,
        size=size,
        status=status,
        type=locker_type,
        passcode="123456" if status != Locker.Status.AVAILABLE else "",
        qr_data="qr-token" if status != Locker.Status.AVAILABLE else "",
        is_door_open=False,
        has_object=status == Locker.Status.OCCUPIED,
        is_locked=True,
    )


@pytest.mark.django_db
def test_full_locker_workflow_records_user_actor_and_resets_state(client, locker, line_user):
    auth = _auth(line_user)

    book_response = client.post(
        "/api/lockers/book/",
        data={"building_id": locker.building_id, "size": locker.size.lower(), "type": locker.type.lower()},
        content_type="application/json",
        **auth,
    )
    assert book_response.status_code == 200
    assert book_response.data["locker_id"] == locker.id
    assert len(book_response.data["passcode"]) == 6

    open_response = client.post(
        f"/api/lockers/{locker.id}/open/",
        data={},
        content_type="application/json",
        **auth,
    )
    assert open_response.status_code == 200
    assert open_response.data["is_door_open"] is True

    deposit_response = client.post(
        f"/api/lockers/{locker.id}/deposit/",
        data={},
        content_type="application/json",
        **auth,
    )
    assert deposit_response.status_code == 200
    assert deposit_response.data["status"] == Locker.Status.OCCUPIED
    assert deposit_response.data["has_object"] is True

    status_response = client.get(
        reverse("user-status") + f"?line_user_id={line_user.line_user_id}",
    )
    assert status_response.status_code == 200
    assert status_response.data["status"] == "HAS_ACTIVE_LOCKER"
    assert status_response.data["lockers"][0]["id"] == locker.id

    verify_response = client.post(
        "/api/lockers/verify-qr/",
        data={"qr_data": book_response.data["qr_data"]},
        content_type="application/json",
        **auth,
    )
    assert verify_response.status_code == 200
    assert verify_response.data["is_door_open"] is True
    assert verify_response.data["is_locked"] is False

    pickup_response = client.post(
        f"/api/lockers/{locker.id}/pickup/",
        data={},
        content_type="application/json",
        **auth,
    )
    assert pickup_response.status_code == 200
    assert pickup_response.data["status"] == Locker.Status.AVAILABLE
    assert pickup_response.data["passcode"] == ""
    assert pickup_response.data["qr_data"] == ""
    assert pickup_response.data["has_object"] is False

    actions = list(
        LockerLog.objects
        .filter(locker=locker)
        .order_by("id")
        .values_list("action", "actor_id")
    )
    assert actions == [
        ("ACTION_BOOK", line_user.line_user_id),
        ("ACTION_OPEN", line_user.line_user_id),
        ("ACTION_DEPOSIT", line_user.line_user_id),
        ("ACTION_VERIFY_QR", line_user.line_user_id),
        ("ACTION_PICKUP", line_user.line_user_id),
    ]


@pytest.mark.django_db
def test_pickup_requires_verified_or_open_locker(client, locker, line_user):
    locker.status = Locker.Status.OCCUPIED
    locker.passcode = "123456"
    locker.qr_data = "qr-token"
    locker.has_object = True
    locker.is_locked = True
    locker.is_door_open = False
    locker.save()

    response = client.post(
        f"/api/lockers/{locker.id}/pickup/",
        data={},
        content_type="application/json",
        **_auth(line_user),
    )

    assert response.status_code == 400
    assert "must be unlocked before pickup" in response.data["error"]


@pytest.mark.django_db
def test_locker_list_filters_match_backend_b_hot_paths(client, building, locker):
    _create_locker(
        building,
        "lck-booked-food",
        local_id="2",
        status=Locker.Status.BOOKED,
        size="M",
        locker_type="FOOD",
    )
    _create_locker(
        building,
        "lck-available-asset",
        local_id="3",
        status=Locker.Status.AVAILABLE,
        size="M",
        locker_type="ASSET",
    )
    _create_locker(
        building,
        "lck-small-food",
        local_id="4",
        status=Locker.Status.AVAILABLE,
        size="S",
        locker_type="FOOD",
    )

    response = client.get(
        f"/api/lockers/?building_id={building.id}&status=available&type=food&size=m"
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.data] == [locker.id]


@pytest.mark.django_db
def test_user_status_active_locker_uses_bounded_queries(client, locker, line_user, django_assert_num_queries):
    locker.status = Locker.Status.OCCUPIED
    locker.save(update_fields=["status"])
    LockerLog.objects.create(locker=locker, action="ACTION_BOOK", actor_id=line_user.line_user_id)
    LockerLog.objects.create(locker=locker, action="ACTION_DEPOSIT", actor_id=line_user.line_user_id)

    with django_assert_num_queries(2):
        response = client.get(reverse("user-status") + f"?line_user_id={line_user.line_user_id}")

    assert response.status_code == 200
    assert response.data["status"] == "HAS_ACTIVE_LOCKER"
    assert response.data["lockers"][0]["id"] == locker.id


@pytest.mark.django_db
def test_admin_cli_list_uses_single_locker_query_after_auth(client, locker, line_user, django_assert_num_queries):
    with django_assert_num_queries(2):
        response = client.post(
            reverse("admin-cli"),
            data={"command": "list --status=available --type=food"},
            content_type="application/json",
            **_auth(line_user),
        )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["lockers"][0]["id"] == locker.id


def test_backend_b_indexes_cover_booking_verification_and_status_paths():
    assert {index.name for index in Locker._meta.indexes} >= {
        "locker_lookup_idx",
        "locker_qr_lookup_idx",
        "locker_pin_lookup_idx",
        "locker_wall_order_idx",
    }
    assert {index.name for index in LockerLog._meta.indexes} >= {
        "lockerlog_actor_locker_idx",
        "lockerlog_locker_created_idx",
    }
