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
]
