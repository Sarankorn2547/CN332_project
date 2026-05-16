import uuid
from django.db import models


class Project(models.Model):
    id = models.TextField(primary_key=True)
    name = models.TextField()
    address = models.TextField()
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name


class Building(models.Model):
    id = models.TextField(primary_key=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="buildings"
    )
    name = models.TextField()
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="rooms"
    )
    unit_number = models.TextField()
    floor = models.TextField()

    def __str__(self):
        return f"{self.unit_number} (Floor {self.floor})"


class Locker(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        BOOKED = "BOOKED", "Booked"
        OCCUPIED = "OCCUPIED", "Occupied"

    id = models.TextField(primary_key=True)
    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="lockers"
    )
    local_id = models.TextField()
    size = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    type = models.TextField()
    metadata = models.JSONField(blank=True, null=True)

    passcode = models.TextField()
    qr_data = models.TextField()

    is_door_open = models.BooleanField(default=False)
    has_object = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=True)

    deposit_start_time = models.BigIntegerField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["building", "status"], name="locker_bldg_status_idx"),
            models.Index(fields=["type", "status"], name="locker_type_status_idx"),
            models.Index(fields=["deposit_start_time"], name="locker_deposit_idx"),
            models.Index(fields=["qr_data"], name="locker_qr_idx"),
            models.Index(fields=["passcode"], name="locker_pin_idx"),
        ]

    def __str__(self):
        return self.id


class LineUser(models.Model):
    id = models.BigAutoField(primary_key=True)

    line_user_id = models.TextField(unique=True)

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="line_users"
    )

    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        related_name="line_users"
    )

    room_no = models.TextField()
    display_name = models.TextField()

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.display_name


class LockerLog(models.Model):
    id = models.BigAutoField(primary_key=True)

    created_at = models.DateTimeField(auto_now_add=True)

    locker = models.ForeignKey(
        Locker,
        on_delete=models.CASCADE,
        related_name="logs"
    )

    action = models.TextField()
    actor_id = models.TextField()

    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["locker", "action"], name="llog_locker_action_idx"),
            models.Index(fields=["actor_id"], name="llog_actor_idx"),
            models.Index(fields=["created_at"], name="llog_created_idx"),
        ]

    def __str__(self):
        return f"{self.action} - {self.locker_id}"
