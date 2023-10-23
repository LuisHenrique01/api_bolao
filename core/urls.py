from django.urls import path

from core.api.viewsets import PaymentsWebhook, TransfersWebhook

urlpatterns = [
    path('webhook/payments/', PaymentsWebhook.as_view()),
    path('webhook/transfers/', TransfersWebhook.as_view()),
]
