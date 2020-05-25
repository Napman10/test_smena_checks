from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^create_checks/$', views.create_checks, name='create_checks'),
    url(r'^rendered_checks/$', views.rendered_checks, name='rendered_checks'),
    url(r'^take_pdf/$', views.take_pdf, name='take_pdf'),
]