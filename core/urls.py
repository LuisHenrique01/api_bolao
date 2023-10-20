from django.urls import path

from core.api.viewsets import PaymentsWebhook

urlpatterns = [
    path('webhook/payments/', PaymentsWebhook.as_view()),
]
