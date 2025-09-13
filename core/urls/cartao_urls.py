from django.urls import path

from ..views import transacao_cartao_views
from ..views.cartao_views import (
    CartaoCreateView,
    CartaoDeleteView,
    CartaoListView,
    CartaoUpdateView,
)
from ..views.fatura_views import (
    FaturaDetailView,
    FaturaListView,
    FaturaPagarView,
    FaturaUpdateView,
)

app_name = "cartoes"

urlpatterns = [
    path("", CartaoListView.as_view(), name="listar_cartoes"),
    path("novo/", CartaoCreateView.as_view(), name="criar_cartao"),
    path("<int:pk>/editar/", CartaoUpdateView.as_view(), name="editar_cartao"),
    path("<int:pk>/excluir/", CartaoDeleteView.as_view(), name="excluir_cartao"),
    # URLs para Faturas de um Cartão
    path("<int:cartao_pk>/faturas/", FaturaListView.as_view(), name="listar_faturas"),
    path("faturas/<int:fatura_pk>/", FaturaDetailView.as_view(), name="detalhe_fatura"),
    path(
        "faturas/<int:fatura_pk>/editar/",
        FaturaUpdateView.as_view(),
        name="editar_fatura",
    ),
    path(
        "faturas/<int:fatura_pk>/pagar/", FaturaPagarView.as_view(), name="pagar_fatura"
    ),
    # URLs para Transações de Cartão
    path(
        "<int:cartao_pk>/lancar-transacao/",
        transacao_cartao_views.lancar_transacao_cartao,
        name="lancar_transacao_cartao",
    ),
    path(
        "transacoes/<int:pk>/editar/",
        transacao_cartao_views.editar_transacao_cartao,
        name="editar_transacao_cartao",
    ),
    path(
        "transacoes/<int:pk>/excluir/",
        transacao_cartao_views.excluir_transacao_cartao,
        name="excluir_transacao_cartao",
    ),
]
