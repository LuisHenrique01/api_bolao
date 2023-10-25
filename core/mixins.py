from rest_framework.response import Response
from rest_framework import status


class WebhookActionMixin:

    def post(self, request, *args, **kwargs):
        default_function = lambda: status.HTTP_200_OK
        event = request.data['event']
        handler = getattr(self, event.lower(), default_function)
        _status = handler()
        print(request.data)
        return Response(status=_status)