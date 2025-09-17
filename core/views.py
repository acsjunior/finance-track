import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import InvoiceForm, InvoicePaymentForm, TransactionForm
from .models import Category, Invoice, Transaction


class MonthlyNavigationMixin:
    """
    Mixin that adds month-based navigation context to views.

    Provides context keys for the current, previous, and next months based on transaction dates.
    Intended for use in views that display monthly financial data.

    Attributes:
        None
    """

    def get_context_data(self, **kwargs):
        """
        Extends context with navigation keys for monthly financial views.

        Adds the current month, previous month (if available), and next month (if available) to the context.
        Navigation is determined by the earliest and latest transaction dates in the database.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the view.

        Returns:
            dict: Context data including navigation keys for current, previous, and next months.

        Context keys added:
            current_month (date): The first day of the selected month.
            prev_month (date, optional): Date for previous month navigation.
            next_month (date, optional): Date for next month navigation.
        """
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)
        current_month_date = datetime.date(year, month, 1)

        context["current_month"] = current_month_date
        first_transaction = Transaction.objects.order_by("date").first()
        if first_transaction and first_transaction.date < current_month_date:
            context["prev_month"] = current_month_date - relativedelta(months=1)

        last_transaction = Transaction.objects.order_by("date").last()
        if last_transaction and last_transaction.date > (
            current_month_date + relativedelta(months=1) - relativedelta(days=1)
        ):
            context["next_month"] = current_month_date + relativedelta(months=1)

        return context


class TransactionListView(MonthlyNavigationMixin, TemplateView):
    """
    Displays a detailed list of all bank account transactions for the selected month, excluding invoice payments.

    Inherits from MonthlyNavigationMixin and uses a simple summary to show monthly balance, income, and expenses.

    Attributes:
        template_name (str): Template used for rendering the transaction list view.
    """

    template_name = "core/transaction_list.html"

    def get_context_data(self, **kwargs):
        """
        Generates context for the detailed transaction view of the selected month.

        Filters and organizes bank account transactions for the month, excluding invoice payments, and prepares data for the template.
        Adds items to the context and calls the mixin method for month navigation keys.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict: Context containing the list of transactions, active view type, and monthly financial summaries.

        Context keys added:
            items (list): List of transaction dictionaries for the month.
            active_view (str): Indicates that the detailed view is active.
            current_month_income (float): Total income for the month.
            current_month_expenses (float): Total expenses for the month.
            monthly_balance (float): Net balance for the month.
            current_month (date): First day of the selected month.
            prev_month (date, optional): Date for previous month navigation.
            next_month (date, optional): Date for next month navigation.
        """
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)

        # Lógica de itens
        transactions = (
            Transaction.objects.filter(date__year=year, date__month=month)
            .exclude(is_invoice_payment=True)
            .order_by("-date")
        )

        items = []
        for transaction in transactions:
            items.append(
                {
                    "date": transaction.date,
                    "description": transaction.description,
                    "category": transaction.category.name
                    if transaction.category
                    else "Sem Categoria",
                    "account_display": transaction.account_display,
                    "amount": transaction.amount,
                    "transaction_type": transaction.transaction_type,
                    "is_invoice": False,
                    "object": transaction,
                }
            )
        context["items"] = items

        # Lógica de resumo simples
        current_month_income = (
            transactions.filter(transaction_type="IN").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        current_month_expenses = (
            transactions.filter(transaction_type="OUT").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )

        context["current_month_income"] = current_month_income
        context["current_month_expenses"] = current_month_expenses
        context["monthly_balance"] = current_month_income - current_month_expenses

        context["active_view"] = "detailed"
        return context


class TransactionConsolidatedView(MonthlyNavigationMixin, TemplateView):
    """
    Displays a consolidated list of all bank account transactions and invoices for the selected month.

    Combines realized and predicted expenses, including paid and unpaid invoices, and provides both real and predicted balances.
    Inherits from MonthlyNavigationMixin to enable month navigation in the context.

    Attributes:
        template_name (str): Template used for rendering the consolidated transaction view.
    """

    template_name = "core/transaction_list.html"

    def get_context_data(self, **kwargs):
        """
        Generates context for the consolidated transaction and invoice view of the selected month.

        Collects bank account transactions and relevant invoices, calculates realized and predicted balances, and prepares data for the template.
        Adds items to the context and calls the mixin method for month navigation keys.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            dict: Context containing the list of transactions and invoices, financial summaries, and navigation keys.

        Context keys added:
            items (list): List of transaction and invoice dictionaries for the month.
            previous_balance (float): Balance before the current month.
            realized_income (float): Total realized income for the month.
            predicted_income (float): Total predicted income for the month.
            realized_expenses (float): Total realized expenses for the month.
            predicted_expenses (float): Total predicted expenses for the month (including unpaid invoices).
            real_balance (float): Realized balance after current month transactions.
            predicted_balance (float): Predicted balance including unpaid invoices.
            active_view (str): Indicates that the consolidated view is active.
            current_month (date): First day of the selected month.
            prev_month (date, optional): Date for previous month navigation.
            next_month (date, optional): Date for next month navigation.
        """
        context = {}
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)
        current_month_date = datetime.date(year, month, 1)

        bank_transactions = Transaction.objects.filter(
            date__year=year,
            date__month=month,
            bank_account__isnull=False,
            is_invoice_payment=False,
        )

        relevant_invoices = Invoice.objects.filter(
            Q(due_date__year=year, due_date__month=month, is_paid=False)
            | Q(payment_date__year=year, payment_date__month=month, is_paid=True)
        )

        items = []
        for transaction in bank_transactions:
            items.append(
                {
                    "date": transaction.date,
                    "description": transaction.description,
                    "category": transaction.category.name
                    if transaction.category
                    else "Sem Categoria",
                    "account_display": transaction.account_display,
                    "amount": transaction.amount,
                    "transaction_type": transaction.transaction_type,
                    "is_invoice": False,
                    "is_predicted": False,
                    "object": transaction,
                }
            )

        for invoice in relevant_invoices:
            display_date = invoice.payment_date if invoice.is_paid else invoice.due_date
            total_amount = (
                invoice.transaction_set.aggregate(Sum("amount"))["amount__sum"] or 0
            )
            items.append(
                {
                    "date": display_date,
                    "description": invoice.display_description,
                    "category": "Cartão de Crédito",
                    "account_display": invoice.credit_card.name,
                    "amount": total_amount,
                    "transaction_type": "OUT",
                    "is_invoice": True,
                    "is_predicted": not invoice.is_paid,
                    "object": invoice,
                }
            )

        context["items"] = sorted(items, key=lambda x: x["date"], reverse=True)

        # Lógica de resumo
        past_transactions = Transaction.objects.filter(
            date__lt=current_month_date,
            bank_account__isnull=False,
        )
        past_income = (
            past_transactions.filter(transaction_type="IN").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        past_expenses = (
            past_transactions.filter(transaction_type="OUT").aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )
        previous_balance = past_income - past_expenses

        realized_income = sum(
            item["amount"]
            for item in items
            if item["transaction_type"] == "IN" and not item.get("is_predicted", False)
        )
        realized_expenses = sum(
            item["amount"]
            for item in items
            if item["transaction_type"] == "OUT" and not item.get("is_predicted", False)
        )

        predicted_expenses_from_invoices = sum(
            item["amount"] for item in items if item.get("is_predicted", False)
        )
        predicted_income = realized_income
        predicted_expenses = realized_expenses + predicted_expenses_from_invoices

        real_balance = previous_balance + realized_income - realized_expenses
        predicted_balance = previous_balance + predicted_income - predicted_expenses

        context.update(
            {
                "previous_balance": previous_balance,
                "realized_income": realized_income,
                "predicted_income": predicted_income,
                "realized_expenses": realized_expenses,
                "predicted_expenses": predicted_expenses,
                "real_balance": real_balance,
                "predicted_balance": predicted_balance,
            }
        )

        context["active_view"] = "consolidated"
        return super().get_context_data(**context)


class TransactionCreateView(CreateView):
    """
    View for creating a new transaction, including support for installment purchases.

    Handles both single and installment transactions. For installment purchases, creates multiple Transaction objects,
    each representing an installment with the correct amount and date.

    Attributes:
        model (Transaction): The model to create.
        form_class (TransactionForm): The form used for transaction creation.
        template_name (str): Template used for rendering the form.
        success_url (str): URL to redirect after successful creation.
    """

    model = Transaction
    form_class = TransactionForm
    template_name = "core/transaction_form.html"
    success_url = reverse_lazy("transaction_list")

    def form_valid(self, form):
        """
        Handles form submission for transaction creation.
        If the transaction is an installment purchase, creates multiple Transaction objects for each installment.
        Otherwise, saves a single transaction using the form.
        Redirects to the success URL after processing.
        """
        cleaned_data = form.cleaned_data
        is_installment = cleaned_data.get("is_installment")

        if is_installment:
            total_amount = cleaned_data.get("amount")
            installments = cleaned_data.get("installments")
            start_date = cleaned_data.get("date")
            description = cleaned_data.get("description")

            installment_amount = round(total_amount / installments, 2)

            for i in range(installments):
                installment_date = start_date + relativedelta(months=i)

                Transaction.objects.create(
                    description=f"{description} ({i + 1}/{installments})",
                    amount=installment_amount,
                    transaction_type=cleaned_data.get("transaction_type"),
                    date=installment_date,
                    category=cleaned_data.get("category"),
                    bank_account=form.instance.bank_account,
                    credit_card=form.instance.credit_card,
                )

            return redirect(self.success_url)
        else:
            self.object = form.save()
            return super().form_valid(form)


class TransactionUpdateView(UpdateView):
    """
    View for updating an existing transaction.

    Attributes:
        model (Transaction): The model to update.
        form_class (TransactionForm): The form used for transaction update.
        template_name (str): Template used for rendering the form.
        success_url (str): URL to redirect after successful update.
    """

    model = Transaction
    form_class = TransactionForm
    template_name = "core/transaction_form.html"
    success_url = reverse_lazy("transaction_list")


class TransactionDeleteView(DeleteView):
    """
    View for deleting a transaction.

    Attributes:
        model (Transaction): The model to delete.
        template_name (str): Template used for rendering the confirmation page.
        success_url (str): URL to redirect after successful deletion.
    """

    model = Transaction
    template_name = "core/transaction_confirm_delete.html"
    success_url = reverse_lazy("transaction_list")


class InvoiceListView(ListView):
    """
    Displays a list of all invoices ordered by due date (descending).

    Attributes:
        model (Invoice): The model to list.
        template_name (str): Template used for rendering.
        context_object_name (str): Name of the context variable for invoices.
    """

    model = Invoice
    template_name = "core/invoice_list.html"
    context_object_name = "invoices"

    def get_queryset(self):
        """
        Returns a queryset of all invoices ordered by due date (descending).
        """
        return Invoice.objects.all().order_by("-due_date")


class InvoiceUpdateView(UpdateView):
    """
    View for updating an existing invoice.

    Attributes:
        model (Invoice): The model to update.
        form_class (InvoiceForm): The form used for invoice update.
        template_name (str): Template used for rendering the form.
        success_url (str): URL to redirect after successful update.
    """

    model = Invoice
    form_class = InvoiceForm
    template_name = "core/invoice_form.html"
    success_url = reverse_lazy("invoice_list")


class InvoiceDetailView(DetailView):
    """
    Displays the details of a single invoice, including its related transactions and total amount.

    Attributes:
        model (Invoice): The model to display.
        template_name (str): Template used for rendering.
        context_object_name (str): Name of the context variable for the invoice.
    """

    model = Invoice
    template_name = "core/invoice_detail.html"
    context_object_name = "invoice"

    def get_context_data(self, **kwargs):
        """
        Extends the context data for the invoice detail view.
        Adds the related transactions and their total amount to the context.
        """
        context = super().get_context_data(**kwargs)
        transactions = self.object.transaction_set.all().order_by("date")
        total = transactions.aggregate(total_amount=Sum("amount"))["total_amount"] or 0

        context["transactions"] = transactions
        context["total"] = total

        return context


class InvoicePaymentView(FormView):
    """
    View for registering the payment of an invoice.

    Displays a form for selecting the payment date and bank account, and creates a transaction to record the payment.

    Context:
        invoice (Invoice): The invoice being paid.
    """

    template_name = "core/invoice_payment_form.html"
    form_class = InvoicePaymentForm

    def get_context_data(self, **kwargs):
        """
        Extends the context data for the invoice payment form view.
        Adds the invoice being paid to the context.

        Context:
            invoice (Invoice): The invoice being paid.
        """
        context = super().get_context_data(**kwargs)
        context["invoice"] = get_object_or_404(Invoice, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        """
        Handles the submission of the invoice payment form.
        Creates a transaction to record the payment, updates the invoice status and payment date, and saves changes.
        Redirects to the success URL after processing.
        """
        invoice = get_object_or_404(Invoice, pk=self.kwargs["pk"])
        payment_date = form.cleaned_data["payment_date"]
        bank_account = form.cleaned_data["bank_account"]

        total_amount = (
            invoice.transaction_set.aggregate(Sum("amount"))["amount__sum"] or 0
        )

        description = invoice.display_description
        payment_category = Category.get_payment_category()

        Transaction.objects.create(
            description=description,
            amount=total_amount,
            transaction_type="OUT",
            date=payment_date,
            bank_account=bank_account,
            category=payment_category,
            is_invoice_payment=True,
        )

        invoice.is_paid = True
        invoice.payment_date = payment_date
        invoice.save()

        return super().form_valid(form)

    def get_success_url(self):
        """
        Returns the URL to redirect to after successful invoice payment.
        """
        return reverse_lazy("invoice_list")
