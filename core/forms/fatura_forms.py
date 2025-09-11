from datetime import date

from django import forms

from ..models import ContaBancaria, Fatura


class FaturaForm(forms.ModelForm):
    class Meta:
        model = Fatura
        fields = ["data_fechamento", "data_vencimento"]
        widgets = {
            "data_fechamento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "data_vencimento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }


class PagamentoFaturaForm(forms.Form):
    conta = forms.ModelChoiceField(
        queryset=ContaBancaria.objects.all(),
        label="Pagar com a Conta",
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="A conta selecionada terá o valor da fatura debitado.",
    )
    data_pagamento = forms.DateField(
        label="Data do Pagamento",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_pagamento"].initial = date.today()
