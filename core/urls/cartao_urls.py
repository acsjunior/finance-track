from django.urls import path

from ..views.cartao_views import (
    CartaoCreateView,
    CartaoDeleteView,
    CartaoListView,
    CartaoUpdateView,
)

app_name = "cartoes"

urlpatterns = [
    path("", CartaoListView.as_view(), name="listar_cartoes"),
    path("novo/", CartaoCreateView.as_view(), name="criar_cartao"),
    path("<int:pk>/editar/", CartaoUpdateView.as_view(), name="editar_cartao"),
    path("<int:pk>/excluir/", CartaoDeleteView.as_view(), name="excluir_cartao"),
]
