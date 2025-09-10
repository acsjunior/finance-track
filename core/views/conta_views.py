from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms import ContaBancariaForm
from ..models import ContaBancaria


class ContaListView(GenericListView):
    model = ContaBancaria
    template_name = "core/contas/listar_contas.html"
    context_object_name = "contas"
    ordering = ["nome"]


class ContaCreateView(GenericCreateView):
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = "core/contas/conta_form.html"
    success_url = reverse_lazy("contas:listar_contas")


class ContaUpdateView(GenericUpdateView):
    model = ContaBancaria
    form_class = ContaBancariaForm
    template_name = "core/contas/conta_form.html"
    success_url = reverse_lazy("contas:listar_contas")


class ContaDeleteView(GenericDeleteView):
    model = ContaBancaria
    success_url = reverse_lazy("contas:listar_contas")
