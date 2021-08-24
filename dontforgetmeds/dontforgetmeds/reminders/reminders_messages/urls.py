from django.conf.urls import url

from . import views

urlpatterns = (
    url(r'^_/status-callback/messages/(?P<ident>\w{40})$', views.status_callback,
        name='status-callback'),
)
