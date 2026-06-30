"""
9.5 — notify users when a lead/task is assigned to them.

We snapshot the old assignee in pre_save and compare in post_save, so we only
notify when the assignee actually changes (and on first assignment at create).
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.crm.models import Lead, Task

from .models import Notification
from .services import notify


def _capture(field):
    def handler(sender, instance, **kwargs):
        if instance.pk:
            old = (
                sender.all_objects.filter(pk=instance.pk)
                .values_list(field, flat=True)
                .first()
            )
        else:
            old = None
        setattr(instance, f"_old_{field}", old)

    return handler


# weak=False: the closures are created inline, so without this Django's weakref
# would garbage-collect the receivers and the old-value capture would never run.
pre_save.connect(
    _capture("owner_id"), sender=Lead, weak=False, dispatch_uid="cap_lead_owner"
)
pre_save.connect(
    _capture("assigned_to_id"),
    sender=Task,
    weak=False,
    dispatch_uid="cap_task_assignee",
)


@receiver(post_save, sender=Lead, dispatch_uid="notify_lead_owner")
def notify_lead_assignment(sender, instance, **kwargs):
    new = instance.owner_id
    if new and new != getattr(instance, "_old_owner_id", None):
        notify(
            tenant=instance.tenant,
            recipient=new,
            type=Notification.Type.ASSIGNED,
            message=f"You were assigned the lead “{instance.name}”.",
            target=instance,
        )


@receiver(post_save, sender=Task, dispatch_uid="notify_task_assignee")
def notify_task_assignment(sender, instance, **kwargs):
    new = instance.assigned_to_id
    if new and new != getattr(instance, "_old_assigned_to_id", None):
        notify(
            tenant=instance.tenant,
            recipient=new,
            type=Notification.Type.ASSIGNED,
            message=f"You were assigned the task “{instance.title}”.",
            target=instance,
        )
