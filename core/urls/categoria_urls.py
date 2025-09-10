from django.urls import path

from ..views.categoria_views import (
    criar_categoria,
    editar_categoria,
    excluir_categoria,
    listar_categorias,
)

app_name = "categorias"

urlpatterns = [
    path("", listar_categorias, name="listar_categorias"),
    path("nova/", criar_categoria, name="criar_categoria"),
    path("<int:pk>/editar/", editar_categoria, name="editar_categoria"),
    path("<int:pk>/excluir/", excluir_categoria, name="excluir_categoria"),
]
