from celery import shared_task

from .services import LockerService


@shared_task(name="foodlocker.tasks.check_abandoned_food_lockers")
def check_abandoned_food_lockers(max_age_seconds=24 * 60 * 60):
    return LockerService.clear_abandoned_food_lockers(
        max_age_seconds=max_age_seconds,
        actor_id="celery",
    )
