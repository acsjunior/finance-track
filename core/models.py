from django.db import models


class Category(models.Model):
    """
    Stores categories to classify transactions (e.g., Food, Transport, Salary).

    Attributes:
        name (CharField): Unique category name.
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="Nome")

    def __str__(self):
        """
        Returns a human-readable string representation of the category (its name).
        """
        return self.name

    class Meta:
        """
        Meta options for the Category model, such as verbose names for admin interface.
        """

        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"


class BankAccount(models.Model):
    """
    Stores checking or savings accounts.

    Attributes:
        name (CharField): Account name.
        balance (DecimalField): Account balance.
    """

    name = models.CharField(max_length=100, verbose_name="Nome da Conta")
    balance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, verbose_name="Saldo"
    )

    def __str__(self):
        """
        Returns a human-readable string representation of the bank account (its name).
        """
        return self.name

    class Meta:
        """
        Meta options for the BankAccount model, such as verbose names for admin interface.
        """

        verbose_name = "Conta Bancária"
        verbose_name_plural = "Contas Bancárias"


class CreditCard(models.Model):
    """
    Stores credit cards.

    Attributes:
        name (CharField): Card name.
        limit (DecimalField): Credit limit.
        due_day (IntegerField): Due day.
        closing_day (IntegerField): Closing day.
    """

    name = models.CharField(max_length=100, verbose_name="Nome do Cartão")
    limit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Limite")
    due_day = models.IntegerField(verbose_name="Dia do Vencimento")
    closing_day = models.IntegerField(verbose_name="Dia do Fechamento")

    def __str__(self):
        """
        Returns a human-readable string representation of the credit card (its name).
        """
        return self.name

    class Meta:
        """
        Meta options for the CreditCard model, such as verbose names for admin interface.
        """

        verbose_name = "Cartão de Crédito"
        verbose_name_plural = "Cartões de Crédito"


class Invoice(models.Model):
    """
    Groups a credit card's transactions within a period.

    Attributes:
        credit_card (ForeignKey): Related credit card.
        start_date (DateField): Start date of the period.
        end_date (DateField): End date of the period.
        due_date (DateField): Due date of the invoice.
        is_paid (BooleanField): Indicates if the invoice is paid.
    """

    credit_card = models.ForeignKey(
        CreditCard, on_delete=models.CASCADE, verbose_name="Cartão de Crédito"
    )
    start_date = models.DateField(verbose_name="Data de Início")
    end_date = models.DateField(verbose_name="Data de Fim")
    due_date = models.DateField(verbose_name="Data de Vencimento")
    is_paid = models.BooleanField(default=False, verbose_name="Paga?")

    def __str__(self):
        """
        Returns a human-readable string representation of the invoice, including card name and due date.
        """
        return f"Fatura de {self.credit_card.name} - Venc: {self.due_date.strftime('%d/%m/%Y')}"

    class Meta:
        """
        Meta options for the Invoice model, such as verbose names for admin interface.
        """

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
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Fatura"
    )

    def __str__(self):
        """
        Returns a human-readable string representation of the transaction, including description and amount.
        """
        return f"{self.description} - R$ {self.amount}"

    class Meta:
        """
        Meta options for the Transaction model, such as verbose names for admin interface.
        """

        verbose_name = "Transação"
        verbose_name_plural = "Transações"
