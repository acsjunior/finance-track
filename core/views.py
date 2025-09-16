import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from .forms import InvoiceForm, TransactionForm
from .models import Invoice, Transaction


class MonthlyViewBase(TemplateView):
    template_name = "core/transaction_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)
        current_month_date = datetime.date(year, month, 1)

        # A classe base assume que a classe filha já forneceu a lista 'items'
        items = context.get("items", [])

        # Lógica de cálculo de saldos (agora centralizada aqui)
        past_transactions = Transaction.objects.filter(date__lt=current_month_date)
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

        current_month_income = sum(
            item["amount"] for item in items if item["transaction_type"] == "IN"
        )
        current_month_expenses = sum(
            item["amount"] for item in items if item["transaction_type"] == "OUT"
        )
        closing_balance = (
            previous_balance + current_month_income - current_month_expenses
        )

        context["previous_balance"] = previous_balance
        context["current_month_income"] = current_month_income
        context["current_month_expenses"] = current_month_expenses
        context["closing_balance"] = closing_balance

        # Lógica de navegação (agora centralizada aqui)
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


# --- CLASSES FILHAS SIMPLIFICADAS ---
class TransactionListView(MonthlyViewBase):
    def get_context_data(self, **kwargs):
        # 1. Pega o contexto da classe mãe (que ainda não tem 'items')
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)

        transactions = Transaction.objects.filter(
            date__year=year, date__month=month
        ).order_by("-date")

        # 2. Cria a lista 'items' específica desta view
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

        # 3. Chama novamente o get_context_data da mãe, que agora com 'items', fará o resto
        return super().get_context_data(**context)


class TransactionConsolidatedView(MonthlyViewBase):
    def get_context_data(self, **kwargs):
        # 1. Pega o contexto da classe mãe
        context = super().get_context_data(**kwargs)
        year = self.kwargs.get("year", timezone.now().year)
        month = self.kwargs.get("month", timezone.now().month)

        bank_transactions = Transaction.objects.filter(
            date__year=year, date__month=month, bank_account__isnull=False
        )
        paid_invoices = Invoice.objects.filter(
            due_date__year=year, due_date__month=month, is_paid=True
        )

        # 2. Cria a lista 'items' específica desta view
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

        # 3. Chama novamente o get_context_data da mãe para fazer o resto
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
