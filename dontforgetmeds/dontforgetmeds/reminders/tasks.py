from __future__ import absolute_import

import traceback

from celery import shared_task
import pytz
import datetime

from django.conf import settings
from django.utils.module_loading import import_string

from .enums import SourceEnum
from .models import Reminder, Instance, Time

@shared_task()
def schedule_reminders():
    """
    Called every X seconds - see ``settings.CELERYBEAT_SCHEDULE``
    """
    timezone='Europe/London'
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    for x in Time.objects.filter(time='%02d:00' % now.astimezone(pytz.timezone(timezone)).hour):
        trigger_reminder.delay(x.reminder_id, SourceEnum.cron.value)

@shared_task()
def trigger_reminder(reminder_id, source=SourceEnum.manual.value):
    """
    Called automatically or when a ``Reminder`` is manually triggered
    """

    reminder = Reminder.objects.get(pk=reminder_id)

    instance = reminder.instances.create(source=source)

    return repr(create_and_trigger_notification(instance))

@shared_task()
def trigger_instance(instance_id):
    """
    Called internally when retrying a ``Reminder``
    """

    instance = Instance.objects.get(pk=instance_id)

    return repr(create_and_trigger_notification(instance))

def create_and_trigger_notification(instance):
    """
    Creates and trigger the appropriate notification for this ``Instance``
    """

    plural = '%ss' % instance.reminder.get_type_enum().name

    # Dynamically create a concrete AbstractNotification based on the type of
    # this Reminder
    notification = getattr(instance, plural).create()

    # Import trigger method for this notification type
    trigger_fn = import_string(
        'takeyourmeds.reminders.reminders_%s.utils.trigger' % plural,
    )

    # We won't get a callback from Twilio if Twilio is disabled, so let's set a
    # special state to not have confusing "in progress" messages outside of a
    # live environment.
    if not settings.TWILIO_ENABLED:
        notification.state = 10 # twilio_disabled

    try:
        twilio_resource = trigger_fn(notification)
    except:
        notification.state = 20 # failed
        notification.traceback = traceback.format_exc()
        raise
    else:
        notification.twilio_sid = twilio_resource.sid
    finally:
        notification.save()

    return notification
