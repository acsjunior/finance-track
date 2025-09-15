from django.urls import path

from . import views

urlpatterns = [
    path("", views.TransactionListView.as_view(), name="transaction_list"),
    path("add/", views.TransactionCreateView.as_view(), name="transaction_add"),
    path(
        "<int:pk>/edit/", views.TransactionUpdateView.as_view(), name="transaction_edit"
    ),
    path(
        "<int:pk>/delete/",
        views.TransactionDeleteView.as_view(),
        name="transaction_delete",
    ),
    # URLs for invoices:
    path("invoices/", views.InvoiceListView.as_view(), name="invoice_list"),
    path(
        "invoices/<int:pk>/edit/",
        views.InvoiceUpdateView.as_view(),
        name="invoice_edit",
    ),
]
