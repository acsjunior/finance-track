from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """
    Stores categories to classify transactions (e.g., Food, Transport, Salary).

    Attributes:
        name (CharField): Unique category name.
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")

    @staticmethod
    def get_payment_category():
        """
        Returns the default category for invoice payments, creating it if it does not exist.

        Returns:
            Category: Instance of the 'Invoice Payment' category.
        """
        category, created = Category.objects.get_or_create(name="Pagamento de Fatura")
        return category

    def __str__(self):
        """
        Returns a human-readable string representation of the category (its name).
        """
        return self.name

    class Meta:
        # Meta options for the Category model, such as verbose names for admin interface.
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"


class Account(models.Model):
    """
    Abstract base model for accounts.

    Attributes:
        name (CharField): Account name.
    """

    name = models.CharField(max_length=100, verbose_name="Nome")

    class Meta:
        # Abstract base class for accounts; not mapped to a database table.
        abstract = True

    def __str__(self):
        return self.name


class BankAccount(Account):
    """
    Stores checking or savings accounts.

    Attributes:
        name (CharField): Bank account name.
        balance (DecimalField): Current account balance.
    """

    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Saldo"
    )

    def __str__(self):
        """
        Returns a human-readable string representation of the bank account (its name).
        """
        return self.name

    class Meta:
        # Meta options for the BankAccount model, such as verbose names for admin interface.
        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"


class CreditCard(Account):
    """
    Stores credit card accounts and their main properties.

    Attributes:
        name (CharField): Credit card name.
        limit (DecimalField): Credit card limit.
        due_day (IntegerField): Payment due day.
        closing_day (IntegerField): Statement closing day.
    """

    limit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Limite")
    due_day = models.IntegerField(verbose_name="Dia do Vencimento")
    closing_day = models.IntegerField(verbose_name="Dia do Fechamento")

    def __str__(self):
        """
        Returns a human-readable string representation of the credit card (its name).
        """
        return self.name

    class Meta:
        # Meta options for the CreditCard model, such as verbose names for admin interface.
        verbose_name = "Cartão de Crédito"
        verbose_name_plural = "Cartões de Crédito"


class Invoice(models.Model):
    """
    Represents a credit card invoice, grouping transactions within a billing period.

    Attributes:
        credit_card (ForeignKey): The credit card associated with this invoice.
        start_date (DateField): Start date of the billing period.
        end_date (DateField): End date of the billing period.
        due_date (DateField): Payment due date for the invoice.
        is_paid (BooleanField): Indicates whether the invoice has been paid.
    """

    credit_card = models.ForeignKey(
        CreditCard, on_delete=models.CASCADE, verbose_name="Cartão de Crédito"
    )
    end_date = models.DateField(verbose_name="Data de Fechamento")
    due_date = models.DateField(verbose_name="Data de Vencimento")
    is_paid = models.BooleanField(default=False, verbose_name="Paga?")
    payment_date = models.DateField(
        null=True, blank=True, verbose_name="Data do Pagamento"
    )

    @property
    def start_date(self):
        """
        Returns the start date of the invoice period.
        If there is a previous invoice, returns the day after its end date;
        otherwise, returns 29 days before the current end date.
        """
        previous_invoice = (
            Invoice.objects.filter(
                credit_card=self.credit_card, end_date__lt=self.end_date
            )
            .order_by("-end_date")
            .first()
        )
        if previous_invoice:
            return previous_invoice.end_date + timedelta(days=1)

        return self.end_date - timedelta(days=29)

    def __str__(self):
        """
        Returns a human-readable string representation of the invoice, including card name and due date.
        """
        return f"Fatura de {self.credit_card.name} - Venc: {self.due_date.strftime('%d/%m/%Y')}"

    class Meta:
        # Meta options for the Invoice model, such as verbose names for admin interface.
        verbose_name = "Fatura"
        verbose_name_plural = "Faturas"


class Transaction(models.Model):
    """
    Records each income or expense.

    Attributes:
        description (CharField): Transaction description.
        amount (DecimalField): Transaction amount.
        transaction_type (CharField): Type (income or expense).
        date (DateField): Transaction date.
        category (ForeignKey): Related category.
        bank_account (ForeignKey): Related bank account.
    """

    TRANSACTION_TYPE_CHOICES = [
        ("IN", "Receita"),
        ("OUT", "Despesa"),
    ]

    description = models.CharField(max_length=255, verbose_name="Descrição")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    transaction_type = models.CharField(
        max_length=3, choices=TRANSACTION_TYPE_CHOICES, verbose_name="Tipo"
    )
    date = models.DateField(verbose_name="Data")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria",
    )

    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Conta Bancária",
    )

    credit_card = models.ForeignKey(
        CreditCard,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Cartão de Crédito",
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Fatura",
    )

    is_invoice_payment = models.BooleanField(
        default=False, verbose_name="É Pagamento de Fatura?"
    )

    @property
    def account_display(self):
        """
        Returns the name of the associated bank account or credit card.
        If neither is set, returns 'N/A'.
        """
        if self.bank_account:
            return self.bank_account.name
        elif self.credit_card:
            return self.credit_card.name
        return "N/A"

    def clean(self):
        """
        Validates that a transaction is associated with either a bank account or a credit card, but not both.
        Raises a ValidationError if both or neither are set.
        """
        super().clean()
        if self.bank_account and self.credit_card:
            raise ValidationError(
                "Uma transação não pode estar associada a uma conta e a um cartão de crédito ao mesmo tempo."
            )
        if not self.bank_account and not self.credit_card:
            raise ValidationError(
                "Uma transação deve estar associada a uma conta ou a um cartão de crédito."
            )

    def save(self, *args, **kwargs):
        """
        Performs full validation and automatically assigns the correct invoice for credit card transactions.
        If the transaction is linked to a credit card, calculates the invoice period and due date,
        creates or retrieves the corresponding Invoice, and sets it on the transaction before saving.
        Calls full_clean() to ensure all model validations are checked before saving.
        """
        self.full_clean()

        if self.credit_card:
            card = self.credit_card
            trans_date = self.date

            if trans_date.day <= card.closing_day:
                invoice_end_date = date(
                    trans_date.year, trans_date.month, card.closing_day
                )
            else:
                next_month = trans_date + relativedelta(months=1)
                invoice_end_date = date(
                    next_month.year, next_month.month, card.closing_day
                )

            if card.due_day > card.closing_day:
                invoice_due_date = date(
                    invoice_end_date.year, invoice_end_date.month, card.due_day
                )
            else:
                due_date_month = invoice_end_date + relativedelta(months=1)
                invoice_due_date = date(
                    due_date_month.year, due_date_month.month, card.due_day
                )

            invoice, created = Invoice.objects.get_or_create(
                credit_card=card,
                end_date=invoice_end_date,
                defaults={"due_date": invoice_due_date},
            )

            self.invoice = invoice

        super().save(*args, **kwargs)

    def __str__(self):
        """
        Returns a human-readable string representation of the transaction, including description and amount.
        """
        return f"{self.description} - R$ {self.amount}"

    class Meta:
        # Meta options for the Transaction model, such as verbose names for admin interface.
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
