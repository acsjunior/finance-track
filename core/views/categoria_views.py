from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms.categoria_forms import CategoriaForm
from ..models import Categoria
from ..views.mixins import FormContextMixin


class CategoriaListView(GenericListView):
    model = Categoria
    template_name = "core/categorias/listar_categorias.html"
    context_object_name = "categorias"
    ordering = ["nome"]


class CategoriaCreateView(FormContextMixin, GenericCreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "core/categorias/categoria_form.html"
    success_url = reverse_lazy("categorias:listar_categorias")
    cancel_url_name = "categorias:listar_categorias"
    titulo = "Nova Categoria"


class CategoriaUpdateView(FormContextMixin, GenericUpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = "core/categorias/categoria_form.html"
    success_url = reverse_lazy("categorias:listar_categorias")
    cancel_url_name = "categorias:listar_categorias"
    titulo = "Editar Categoria"


class CategoriaDeleteView(GenericDeleteView):
    model = Categoria
    success_url = reverse_lazy("categorias:listar_categorias")
