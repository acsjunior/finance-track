from dateutil.relativedelta import relativedelta
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import TransactionForm
from .models import Transaction


class TransactionListView(ListView):
    """
    Displays a list of all transactions ordered by date (descending).

    Attributes:
        model (Transaction): The model to list.
        template_name (str): Template used for rendering.
        context_object_name (str): Name of the context variable for transactions.
    """

    model = Transaction
    template_name = "core/transaction_list.html"
    context_object_name = "transactions"

    def get_queryset(self):
        """
        Returns a queryset of all transactions ordered by date (descending).
        """
        return Transaction.objects.all().order_by("-date")


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
