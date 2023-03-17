from typing import Any, Dict
from django import forms

from bolao.models import PalpitePlacar


class PalpitePlacarForm(forms.ModelForm):

    class Meta:
        model = PalpitePlacar
        exclude = ('palpite', )
