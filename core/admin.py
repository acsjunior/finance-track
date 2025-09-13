from django.contrib import admin

from .models import BankAccount, Category, CreditCard, Invoice, Transaction


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """
    Admin configuration for BankAccount model.
    Displays account name and balance in the admin list view.
    """

    list_display = ("name", "balance")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Category model.
    Enables search by category name in the admin interface.
    """

    search_fields = ("name",)


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    """
    Admin configuration for CreditCard model.
    Displays card details in the admin list view.
    """

    list_display = ("name", "limit", "due_day", "closing_day")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for Invoice model.
    Displays invoice details and enables filtering by payment status and credit card.
    """

    list_display = ("credit_card", "due_date", "is_paid")
    list_filter = ("is_paid", "credit_card")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transaction model.
    Displays transaction details, enables filtering and searching in the admin interface.
    """

    list_display = ("description", "amount", "date", "category", "transaction_type")
    list_filter = ("transaction_type", "date", "category")
    search_fields = ("description",)
