from django import forms

from .models import BankAccount, CreditCard, Invoice, Transaction


class TransactionForm(forms.ModelForm):
    """
    Form for creating and validating Transaction instances, including support for installment purchases.

    Provides fields for selecting a bank account or credit card, and for specifying installment options.
    Custom validation ensures that required fields are set correctly for both single and installment transactions.
    """

    is_installment = forms.BooleanField(
        label="É compra parcelada?",
        required=False,
    )

    installments = forms.IntegerField(
        label="Número de Parcelas",
        required=False,
        min_value=2,
    )

    installment_frequency = forms.ChoiceField(
        label="Frequência",
        required=False,
        choices=[
            ("monthly", "Mensal"),
        ],
    )

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
        Performs custom validation for the transaction form.
        Sets the bank_account or credit_card on the instance based on the selected account_choice.
        Validates required fields for installment purchases (installments and frequency).
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

        is_installment = cleaned_data.get("is_installment")
        installments = cleaned_data.get("installments")
        frequency = cleaned_data.get("installment_frequency")

        if is_installment:
            if not installments:
                self.add_error(
                    "installments", "Este campo é obrigatório para compras parceladas."
                )
            if not frequency:
                self.add_error(
                    "installment_frequency",
                    "Este campo é obrigatório para compras parceladas.",
                )

        return cleaned_data


class InvoiceForm(forms.ModelForm):
    """
    Form for creating and updating Invoice instances.

    Provides fields for editing the end date, due date, and payment status of an invoice.
    """

    class Meta:
        # Configuration for InvoiceForm: model, fields, and widgets.
        model = Invoice
        fields = ["end_date", "due_date", "is_paid"]
        widgets = {
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }
