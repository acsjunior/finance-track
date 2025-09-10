from django import forms

from ..models import ContaBancaria


class ContaBancariaForm(forms.ModelForm):
    class Meta:
        model = ContaBancaria
        fields = ["nome", "saldo_inicial"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "saldo_inicial": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
        }
