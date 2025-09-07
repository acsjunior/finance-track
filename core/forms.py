# core/forms.py
from django import forms

from .models import Transacao


class TransacaoBaseForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ["descricao", "categoria", "valor", "data", "data_pagamento"]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "data_pagamento": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "descricao": forms.TextInput(
                attrs={
                    "placeholder": "Ex: Salário, Aluguel...",
                    "class": "form-control",
                }
            ),
            "categoria": forms.Select(attrs={"class": "form-control"}),
            "valor": forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
        }


class ReceitaForm(TransacaoBaseForm):
    class Meta(TransacaoBaseForm.Meta):
        fields = ["descricao", "categoria", "valor", "data"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "E"
        instance.data_pagamento = instance.data
        if commit:
            instance.save()
        return instance


class DespesaForm(TransacaoBaseForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "S"
        if commit:
            instance.save()
        return instance


class TransacaoForm(TransacaoBaseForm):
    class Meta(TransacaoBaseForm.Meta):
        fields = TransacaoBaseForm.Meta.fields + ["tipo"]
