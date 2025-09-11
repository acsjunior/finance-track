from django.urls import include, path

from . import main_views

urlpatterns = [
    # Quando a URL estiver vazia (''), chame a função 'dashboard' de views.py
    path("", main_views.dashboard, name="dashboard"),
    path(
        "api/adicionar-categoria/",
        main_views.adicionar_categoria_api,
        name="adicionar_categoria_api",
    ),
    path("excluir/<int:pk>/", main_views.excluir_transacao, name="excluir_transacao"),
    path("editar/<int:pk>/", main_views.editar_transacao, name="editar_transacao"),
    path(
        "cartoes/<int:cartao_pk>/faturas/",
        main_views.listar_faturas,
        name="listar_faturas",
    ),
    path("faturas/<int:fatura_pk>/", main_views.detalhe_fatura, name="detalhe_fatura"),
    path(
        "faturas/<int:fatura_pk>/editar/",
        main_views.editar_fatura,
        name="editar_fatura",
    ),
    path(
        "cartoes/<int:pk>/lancar-transacao/",
        main_views.lancar_transacao_cartao,
        name="lancar_transacao_cartao",
    ),
    path(
        "faturas/<int:fatura_pk>/pagar/", main_views.pagar_fatura, name="pagar_fatura"
    ),
    path(
        "transacoes-cartao/<int:pk>/editar/",
        main_views.editar_transacao_cartao,
        name="editar_transacao_cartao",
    ),
    path(
        "transacoes-cartao/<int:pk>/excluir/",
        main_views.excluir_transacao_cartao,
        name="excluir_transacao_cartao",
    ),
    path("contas/", include("core.urls.conta_urls")),
    path("categorias/", include("core.urls.categoria_urls")),
    path("cartoes/", include("core.urls.cartao_urls")),
]
