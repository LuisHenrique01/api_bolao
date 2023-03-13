from uuid import uuid4
from django.db import models


class BaseModel(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    created = models.DateTimeField('Criado em', auto_now_add=True)
    updated = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        abstract = True
