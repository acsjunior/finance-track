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
    path("contas/", include("core.urls.conta_urls")),
    path("categorias/", include("core.urls.categoria_urls")),
    path("cartoes/", include("core.urls.cartao_urls")),
]
