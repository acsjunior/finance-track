from django.urls import path

from ..views.conta_views import (
    ContaCreateView,
    ContaDeleteView,
    ContaListView,
    ContaUpdateView,
)

app_name = "contas"

urlpatterns = [
    path("", ContaListView.as_view(), name="listar_contas"),
    path("nova/", ContaCreateView.as_view(), name="criar_conta"),
    path("<int:pk>/editar/", ContaUpdateView.as_view(), name="editar_conta"),
    path("<int:pk>/excluir/", ContaDeleteView.as_view(), name="excluir_conta"),
]
