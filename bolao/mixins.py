from rest_framework import status
from rest_framework.response import Response

class ListCreateDetailOnlyMixin:
    def update(self, request, *args, **kwargs):
        return Response({'detail': 'Atualização não permitida.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({'detail': 'Atualização parcial não permitida.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Exclusão não permitida.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
