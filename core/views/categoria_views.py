from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms.categoria_forms import CategoriaForm
from ..models import Categoria
from ..views.mixins import FormContextMixin, ListContextMixin


class CategoriaListView(ListContextMixin, GenericListView):
    model = Categoria
    template_name = "core/categorias/listar_categorias.html"
    context_object_name = "categorias"
    ordering = ["nome"]
    titulo = "Minhas Categorias"
    criar_url_name = "categorias:criar_categoria"
    criar_label = "Adicionar Nova Categoria"
    editar_url_name = "categorias:editar_categoria"
    excluir_url_name = "categorias:excluir_categoria"
    headers = ["Nome da Categoria", "Ícone"]
    fields = ["nome", "icone"]
    empty_message = "Nenhuma categoria cadastrada."


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
