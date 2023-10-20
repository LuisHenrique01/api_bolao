from django_filters import rest_framework as filters
from bolao import STATUS_BOLAO

from bolao.models import Bolao

class BolaoFilter(filters.FilterSet):
    taxa_banca__gte = filters.NumberFilter(field_name="taxa_banca", lookup_expr="gte")
    taxa_banca__lte = filters.NumberFilter(field_name="taxa_banca", lookup_expr="lte")
    taxa_criador__gte = filters.NumberFilter(field_name="taxa_criador", lookup_expr="gte")
    taxa_criador__lte = filters.NumberFilter(field_name="taxa_criador", lookup_expr="lte")
    bilhetes_minimos__gte = filters.NumberFilter(field_name="bilhetes_minimos", lookup_expr="gte")
    bilhetes_minimos__lte = filters.NumberFilter(field_name="bilhetes_minimos", lookup_expr="lte")
    criador__username = filters.CharFilter(field_name="criador__username", lookup_expr="exact")
    criador__nome = filters.CharFilter(field_name="criador__nome", lookup_expr="startswith")

    class Meta:
        model = Bolao
        fields = ['estorno']
