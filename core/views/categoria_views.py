from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms.categoria_forms import CategoriaForm
from ..models import Categoria


class CategoriaListView(GenericListView):
    model = Categoria
    template_name = "core/categorias/listar_categorias.html"
    context_object_name = "categorias"
    ordering = ["nome"]


class CategoriaCreateView(GenericCreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "core/categorias/categoria_form.html"
    success_url = reverse_lazy("categorias:listar_categorias")


class CategoriaUpdateView(GenericUpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "core/categorias/categoria_form.html"
    success_url = reverse_lazy("categorias:listar_categorias")


class CategoriaDeleteView(GenericDeleteView):
    model = Categoria
    success_url = reverse_lazy("categorias:listar_categorias")
