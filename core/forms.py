from django import forms

from .models import Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            "description",
            "amount",
            "transaction_type",
            "date",
            "category",
            "bank_account",
            "invoice",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }
