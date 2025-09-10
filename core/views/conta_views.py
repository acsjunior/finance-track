from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms import ContaBancariaForm
from ..models import ContaBancaria
from ..views.mixins import FormContextMixin


class ContaListView(GenericListView):
    model = ContaBancaria
    template_name = "core/contas/listar_contas.html"
    context_object_name = "contas"
    ordering = ["nome"]


class ContaCreateView(FormContextMixin, GenericCreateView):
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = "core/contas/conta_form.html"
    success_url = reverse_lazy("contas:listar_contas")
    cancel_url_name = "contas:listar_contas"
    titulo = "Nova Conta"


class ContaUpdateView(FormContextMixin, GenericUpdateView):
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = "core/contas/conta_form.html"
    success_url = reverse_lazy("contas:listar_contas")
    cancel_url_name = "contas:listar_contas"
    titulo = "Editar Conta"


class ContaDeleteView(GenericDeleteView):
    model = ContaBancaria
    success_url = reverse_lazy("contas:listar_contas")
