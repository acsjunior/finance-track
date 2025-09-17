import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
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
from .models import Invoice, Transaction


class MonthlyViewBase(TemplateView):
    """
    Abstract base view that centralizes logic for monthly financial summaries and navigation.

    Provides reusable calculations for current month income and expenses, previous balance, closing balance,
    and month navigation. Child views must supply a list of items (transactions/invoices) in the context.

    Attributes:
        template_name (str): Template used for rendering the monthly view.
        summary_type (str): Type of summary, either 'full' or 'simple'.
    """

    template_name = "core/transaction_list.html"
    summary_type = "full"  # 'full' or 'simple'

    def get_context_data(self, **kwargs):
        """
        Extends and enriches the context data for monthly financial views.

        Calculates current month income and expenses, previous balance, closing balance, and navigation dates.
        Adds summary values to the context based on the summary_type ('full' or 'simple').

        Args:
            **kwargs: Arbitrary keyword arguments passed to the view.

        Returns:
            dict: Context data including financial summaries and navigation keys.

        Context keys added:
            items (list): List of transaction/invoice dictionaries for the month.
            current_month_income (float): Total income for the current month.
            current_month_expenses (float): Total expenses for the current month.
            monthly_balance (float, optional): Net balance for the month (simple summary).
            previous_balance (float, optional): Balance before the current month (full summary).
            closing_balance (float, optional): Final balance after current month transactions (full summary).
            current_month (date): The first day of the selected month.
            prev_month (date, optional): Date for previous month navigation.
            next_month (date, optional): Date for next month navigation.
        """
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)
        current_month_date = datetime.date(year, month, 1)
        items = context.get("items", [])

        current_month_income = sum(
            item["amount"] for item in items if item["transaction_type"] == "IN"
        )
        current_month_expenses = sum(
            item["amount"] for item in items if item["transaction_type"] == "OUT"
        )

        context["current_month_income"] = current_month_income
        context["current_month_expenses"] = current_month_expenses

        # Conditional logic based on summary_type "switch"
        if self.summary_type == "simple":
            context["monthly_balance"] = current_month_income - current_month_expenses

        elif self.summary_type == "full":
            past_transactions = Transaction.objects.filter(date__lt=current_month_date)
            past_income = (
                past_transactions.filter(transaction_type="IN").aggregate(
                    Sum("amount")
                )["amount__sum"]
                or 0
            )
            past_expenses = (
                past_transactions.filter(transaction_type="OUT").aggregate(
                    Sum("amount")
                )["amount__sum"]
                or 0
            )
            previous_balance = past_income - past_expenses
            closing_balance = (
                previous_balance + current_month_income - current_month_expenses
            )

            context["previous_balance"] = previous_balance
            context["closing_balance"] = closing_balance

        # Navigation logic
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


class TransactionListView(MonthlyViewBase):
    """
    Displays a detailed list of all bank account transactions for the selected month, excluding invoice payments.

    Inherits from MonthlyViewBase and uses the simple summary to show monthly balance, income, and expenses.

    Attributes:
        summary_type (str): Type of financial summary displayed ('simple').
    """

    summary_type = "simple"

    def get_context_data(self, **kwargs):
        """
        Generates the context for the detailed view of transactions for the selected month.

        Filters and organizes bank transactions for the month, excluding invoice payments, and prepares the data for the template.
        Adds the items to the context and calls the base class method for financial calculations.

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
            prev_month (date, optional): Date for navigation to the previous month.
            next_month (date, optional): Date for navigation to the next month.
        """
        context = {}
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)

        transactions = (
            Transaction.objects.filter(date__year=year, date__month=month)
            .exclude(description__startswith="Pagamento Fatura")
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
        context["active_view"] = "detailed"

        return super().get_context_data(**context)


class TransactionConsolidatedView(MonthlyViewBase):
    """
    Displays a consolidated list of all bank account transactions and paid invoices for the selected month.

    Context:
        items (list): List of transaction and invoice dictionaries for the month.
        active_view (str): Indicates that the consolidated view is active.
        previous_balance (float): Balance before the current month.
        current_month_income (float): Total income for the current month.
        current_month_expenses (float): Total expenses for the current month.
        closing_balance (float): Final balance after current month transactions.
        current_month (date): The first day of the selected month.
        prev_month (date, optional): Date for previous month navigation.
        next_month (date, optional): Date for next month navigation.
    """

    def get_context_data(self, **kwargs):
        """ "
        Extends the context data with a consolidated list of bank transactions and paid invoices for the month.
        Calls the parent method to add financial calculations and navigation logic.
        Child views must provide 'items' in the context, which is a list of dictionaries
        representing transactions and/or invoices for the current month.
        """
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)

        bank_transactions = Transaction.objects.filter(
            date__year=year, date__month=month, bank_account__isnull=False
        )
        paid_invoices = Invoice.objects.filter(
            due_date__year=year, due_date__month=month, is_paid=True
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
                    "object": transaction,
                }
            )
        for invoice in paid_invoices:
            total_amount = (
                invoice.transaction_set.aggregate(Sum("amount"))["amount__sum"] or 0
            )
            items.append(
                {
                    "date": invoice.due_date,
                    "description": f"Pagamento Fatura {invoice.credit_card.name}",
                    "category": "Cartão de Crédito",
                    "account_display": invoice.credit_card.name,
                    "amount": total_amount,
                    "transaction_type": "OUT",
                    "is_invoice": True,
                    "object": invoice,
                }
            )

        context["items"] = sorted(items, key=lambda x: x["date"], reverse=True)
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

        Transaction.objects.create(
            description=f"Pagamento Fatura {invoice.credit_card.name}",
            amount=total_amount,
            transaction_type="OUT",
            date=payment_date,
            bank_account=bank_account,
            category=None,
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
