import os

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


class AsaasWebhook(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)