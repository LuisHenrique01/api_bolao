from rest_framework.response import Response
from rest_framework import status


class WebhookActionMixin:

    def post(self, request, *args, **kwargs):
        event = request.data['event']
        handler = getattr(self, event.lower(), lambda: status.HTTP_200_OK)
        _status = handler()
        return Response(status=_status)
