from django import forms

from bolao.models import Palpite


class PalpitePlacarForm(forms.ModelForm):

    class Meta:
        model = Palpite
        exclude = ('bilhete', )
