from django.urls import path
from . import views

urlpatterns = [
    path("summarize/", views.summarize_report, name="summarize_report"),
]
