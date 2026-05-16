import pytest
from django.urls import reverse

from foodlocker.models import Locker, LockerLog


def _auth(client, line_user):
    response = client.post(
        reverse("token-obtain"),
        data={"line_user_id": line_user.line_user_id},
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {response.data['access']}"}


@pytest.mark.django_db
def test_full_locker_workflow_via_api(client, locker, line_user, settings):
    settings.LOCKER_WEBSOCKET_BROADCAST_ENABLED = False
    auth = _auth(client, line_user)

    book_response = client.post(
        "/api/lockers/book/",
        data={
            "building_id": locker.building_id,
            "size": locker.size,
            "type": locker.type,
        },
        content_type="application/json",
        **auth,
    )
    assert book_response.status_code == 200
    qr_data = book_response.data["qr_data"]
    passcode = book_response.data["passcode"]

    locker.refresh_from_db()
    assert locker.status == Locker.Status.BOOKED
    assert locker.qr_data == qr_data
    assert locker.passcode == passcode

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

    verify_response = client.post(
        "/api/lockers/verify-qr/",
        data={"qr_data": qr_data},
        content_type="application/json",
        **auth,
    )
    assert verify_response.status_code == 200
    assert verify_response.data["is_door_open"] is True
    assert verify_response.data["is_locked"] is False

    pickup_response = client.post(
        f"/api/lockers/{locker.id}/pickup/",
        data={"actor_id": line_user.line_user_id},
        content_type="application/json",
        **auth,
    )
    assert pickup_response.status_code == 200
    assert pickup_response.data["status"] == Locker.Status.AVAILABLE
    assert pickup_response.data["passcode"] == ""
    assert pickup_response.data["qr_data"] == ""
    assert pickup_response.data["deposit_start_time"] is None

    actions = list(
        LockerLog.objects.filter(locker=locker).order_by("id").values_list("action", flat=True)
    )
    assert actions == [
        "ACTION_BOOK",
        "ACTION_OPEN",
        "ACTION_DEPOSIT",
        "ACTION_VERIFY_QR",
        "ACTION_PICKUP",
    ]
