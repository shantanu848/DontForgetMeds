import datetime

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .enums import StateEnum
from .models import Message

@csrf_exempt
@require_POST
def status_callback(request, ident):

    message = get_object_or_404(Message, ident=ident)

    try:
        message.state = {
            'accepted': StateEnum.sending,
            'queued': StateEnum.sending,
            'sending': StateEnum.sending,
            'sent': StateEnum.sent,
            'delivered': StateEnum.delivered,
            'failed': StateEnum.failed,
            'undelivered': StateEnum.failed,
        }[request.POST['MessageStatus']]
    except KeyError:
        message.state = StateEnum.unknown

    message.state_updated = datetime.datetime.utcnow()

    message.save(update_fields=('state', 'state_updated'))

    return HttpResponse('')
