# core/forms.py
from django import forms

from .models import Transacao


# FORMULÁRIO BASE
class TransacaoBaseForm(forms.ModelForm):
    class Meta:
        model = Transacao
        # CORREÇÃO ESTÁ NESTA LINHA: trocamos 'pago' por 'data_pagamento'
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


# FORMULÁRIO DE RECEITA (Não precisa de 'data_pagamento' na criação)
class ReceitaForm(TransacaoBaseForm):
    class Meta(TransacaoBaseForm.Meta):
        fields = ["descricao", "categoria", "valor", "data"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "E"
        instance.data_pagamento = instance.data  # Define o pagamento na data da receita
        if commit:
            instance.save()
        return instance


# FORMULÁRIO DE DESPESA
class DespesaForm(TransacaoBaseForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "S"
        if commit:
            instance.save()
        return instance


# FORMULÁRIO DE EDIÇÃO (precisa de todos os campos)
class TransacaoForm(TransacaoBaseForm):
    class Meta(TransacaoBaseForm.Meta):
        fields = TransacaoBaseForm.Meta.fields + ["tipo"]
