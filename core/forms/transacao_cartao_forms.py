from django import forms

from ..models import Fatura, TransacaoCartao


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
