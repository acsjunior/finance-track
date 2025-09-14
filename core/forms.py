from django import forms

from .models import BankAccount, CreditCard, Transaction


class TransactionForm(forms.ModelForm):
    """
    Form for creating and validating Transaction instances.

    Provides a choice field for selecting either a bank account or a credit card,
    and custom validation to ensure one is selected and set correctly.
    """

    account_choice = forms.ChoiceField(
        label="Conta / Cartão",
        required=True,
        choices=[],
    )

    class Meta:
        # Configuration for TransactionForm: model, fields, and widgets.
        model = Transaction
        fields = [
            "description",
            "amount",
            "transaction_type",
            "date",
            "category",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initializes the form and sets choices for the account_choice field,
        grouping available bank accounts and credit cards for selection.
        """
        super().__init__(*args, **kwargs)

        bank_accounts = [
            (f"bankaccount_{acc.pk}", acc.name) for acc in BankAccount.objects.all()
        ]
        credit_cards = [
            (f"creditcard_{card.pk}", card.name) for card in CreditCard.objects.all()
        ]

        self.fields["account_choice"].choices = [
            ("", "---------"),
            ("Contas Bancárias", bank_accounts),
            ("Cartões de Crédito", credit_cards),
        ]

    def clean(self):
        """
        Custom validation for the form.
        Sets the bank_account or credit_card on the instance based on the selected account_choice.
        Returns the cleaned data dictionary.
        """
        cleaned_data = super().clean()
        account_choice = cleaned_data.get("account_choice")

        if account_choice:
            account_type, account_id = account_choice.split("_")

            if account_type == "bankaccount":
                self.instance.bank_account = BankAccount.objects.get(pk=account_id)
                self.instance.credit_card = None
            elif account_type == "creditcard":
                self.instance.credit_card = CreditCard.objects.get(pk=account_id)
                self.instance.bank_account = None

        return cleaned_data
