from django.conf import settings
from django.conf.urls import include, url
from django.views.static import serve

urlpatterns = (
    url(r'', include('takeyourmeds.reminders.urls',
        namespace='reminders')),
)

if settings.DEBUG:
    urlpatterns += (
        url(r'^storage/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    )
