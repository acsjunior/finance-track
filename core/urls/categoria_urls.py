from django.urls import path

from ..views.categoria_views import (
    CategoriaCreateView,
    CategoriaDeleteView,
    CategoriaListView,
    CategoriaUpdateView,
)

app_name = "categorias"

urlpatterns = [
    path("", CategoriaListView.as_view(), name="listar_categorias"),
    path("nova/", CategoriaCreateView.as_view(), name="criar_categoria"),
    path("<int:pk>/editar/", CategoriaUpdateView.as_view(), name="editar_categoria"),
    path("<int:pk>/excluir/", CategoriaDeleteView.as_view(), name="excluir_categoria"),
]
