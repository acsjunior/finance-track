# core/forms.py
from django import forms

from .models import ContaBancaria, Transacao


class TransacaoBaseForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ["descricao", "categoria", "valor", "data", "data_pagamento", "conta"]
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
            "conta": forms.Select(attrs={"class": "form-control"}),
        }


class ReceitaForm(TransacaoBaseForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["conta"].required = True

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "E"
        if not instance.data_pagamento:
            instance.data_pagamento = instance.data
        if commit:
            instance.save()
        return instance


class DespesaForm(TransacaoBaseForm):
    def clean(self):
        cleaned_data = super().clean()
        data_pagamento = cleaned_data.get("data_pagamento")
        conta = cleaned_data.get("conta")

        if data_pagamento and not conta:
            raise forms.ValidationError(
                "Para uma despesa paga, você deve selecionar uma conta bancária."
            )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "S"
        if commit:
            instance.save()
        return instance


class TransacaoForm(TransacaoBaseForm):
    class Meta(TransacaoBaseForm.Meta):
        fields = TransacaoBaseForm.Meta.fields + ["tipo"]

    def clean(self):
        cleaned_data = super().clean()
        data_pagamento = cleaned_data.get("data_pagamento")
        conta = cleaned_data.get("conta")
        tipo = cleaned_data.get("tipo")

        if tipo == "S" and data_pagamento and not conta:
            raise forms.ValidationError(
                "Para uma despesa paga, você deve selecionar uma conta bancária."
            )
        if tipo == "E" and not conta:
            raise forms.ValidationError(
                "Para uma receita, você deve selecionar uma conta bancária."
            )

        return cleaned_data


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
