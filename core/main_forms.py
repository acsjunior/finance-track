# core/forms.py
from datetime import date

from django import forms

from .models import ContaBancaria, Fatura, Transacao, TransacaoCartao


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


class TransacaoCartaoBaseForm(forms.ModelForm):
    fatura_manual = forms.ModelChoiceField(
        queryset=Fatura.objects.none(),
        required=False,
        label="Atribuir à Fatura (opcional)",
        empty_label="-- Lançamento Automático --",
    )

    class Meta:
        model = TransacaoCartao
        fields = [
            "descricao",
            "valor",
            "categoria",
            "data",
            "fatura_manual",
        ]
        widgets = {
            "descricao": forms.TextInput(attrs={"class": "form-control"}),
            "valor": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "fatura_manual": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        cartao = kwargs.pop("cartao", None)
        super().__init__(*args, **kwargs)
        if cartao:
            self.fields["fatura_manual"].queryset = Fatura.objects.filter(
                cartao=cartao
            ).order_by("-mes_referencia")


class DespesaCartaoForm(TransacaoCartaoBaseForm):
    numero_parcelas = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Número de Parcelas",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    class Meta(TransacaoCartaoBaseForm.Meta):
        fields = TransacaoCartaoBaseForm.Meta.fields + ["numero_parcelas"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.valor = abs(instance.valor)
        if commit:
            instance.save()
        return instance


class ReceitaCartaoForm(TransacaoCartaoBaseForm):
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.valor = -abs(instance.valor)
        if commit:
            instance.save()
        return instance


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
