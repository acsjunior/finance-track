from django import forms

from core.models import CartaoCredito


class CartaoCreditoForm(forms.ModelForm):
    class Meta:
        model = CartaoCredito
        fields = ["nome", "limite", "dia_fechamento", "dia_vencimento"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "limite": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01"}
            ),
            "dia_fechamento": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "31"}
            ),
            "dia_vencimento": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "max": "31"}
            ),
        }
