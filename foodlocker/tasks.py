try:
    from celery import shared_task
except ModuleNotFoundError as exc:
    if exc.name != "celery":
        raise

    def shared_task(*decorator_args, **decorator_kwargs):
        def decorate(func):
            func.delay = func
            func.apply_async = lambda args=None, kwargs=None, **options: func(
                *(args or ()),
                **(kwargs or {}),
            )
            return func

        if decorator_args and callable(decorator_args[0]) and len(decorator_args) == 1:
            return decorate(decorator_args[0])
        return decorate

from .services import LockerService


@shared_task(name="foodlocker.check_abandoned_food_lockers")
def check_abandoned_food_lockers(threshold_seconds=24 * 60 * 60, now=None):
    return LockerService.check_abandoned_food_lockers(
        threshold_seconds=threshold_seconds,
        now=now,
        actor_id="celery",
    )
