from django.urls import path

from . import views

urlpatterns = [
    # Quando a URL estiver vazia (''), chame a função 'dashboard' de views.py
    path("", views.dashboard, name="dashboard"),
    path(
        "api/adicionar-categoria/",
        views.adicionar_categoria_api,
        name="adicionar_categoria_api",
    ),
    path("excluir/<int:pk>/", views.excluir_transacao, name="excluir_transacao"),
    path("editar/<int:pk>/", views.editar_transacao, name="editar_transacao"),
    path("contas/", views.listar_contas, name="listar_contas"),
    path("contas/nova/", views.criar_conta, name="criar_conta"),
    path("contas/editar/<int:pk>/", views.editar_conta, name="editar_conta"),
    path("contas/excluir/<int:pk>/", views.excluir_conta, name="excluir_conta"),
    path("cartoes/", views.listar_cartoes, name="listar_cartoes"),
    path("cartoes/novo/", views.criar_cartao, name="criar_cartao"),
    path("cartoes/<int:pk>/editar/", views.editar_cartao, name="editar_cartao"),
    path("cartoes/<int:pk>/excluir/", views.excluir_cartao, name="excluir_cartao"),
    path(
        "cartoes/<int:cartao_pk>/faturas/", views.listar_faturas, name="listar_faturas"
    ),
    path("faturas/<int:fatura_pk>/", views.detalhe_fatura, name="detalhe_fatura"),
    path("faturas/<int:fatura_pk>/editar/", views.editar_fatura, name="editar_fatura"),
    path(
        "cartoes/<int:pk>/lancar-transacao/",
        views.lancar_transacao_cartao,
        name="lancar_transacao_cartao",
    ),
    path("faturas/<int:fatura_pk>/pagar/", views.pagar_fatura, name="pagar_fatura"),
    path(
        "transacoes-cartao/<int:pk>/editar/",
        views.editar_transacao_cartao,
        name="editar_transacao_cartao",
    ),
    path(
        "transacoes-cartao/<int:pk>/excluir/",
        views.excluir_transacao_cartao,
        name="excluir_transacao_cartao",
    ),
]
