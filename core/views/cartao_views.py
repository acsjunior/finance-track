from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms import CartaoCreditoForm
from ..models import CartaoCredito
from ..views.mixins import FormContextMixin


class CartaoListView(GenericListView):
    model = CartaoCredito
    template_name = "core/cartoes/listar_cartoes.html"
    context_object_name = "cartoes"
    ordering = ["nome"]


class CartaoCreateView(FormContextMixin, GenericCreateView):
    model = CartaoCredito
    form_class = CartaoCreditoForm
    template_name = "core/cartoes/cartao_form.html"
    success_url = reverse_lazy("cartoes:listar_cartoes")
    cancel_url_name = "cartoes:listar_cartoes"
    titulo = "Novo Cartão"


class CartaoUpdateView(FormContextMixin, GenericUpdateView):
    model = CartaoCredito
    form_class = CartaoCreditoForm
    template_name = "core/cartoes/cartao_form.html"
    success_url = reverse_lazy("cartoes:listar_cartoes")
    cancel_url_name = "cartoes:listar_cartoes"
    titulo = "Editar Cartão"


class CartaoDeleteView(GenericDeleteView):
    model = CartaoCredito
    success_url = reverse_lazy("cartoes:listar_cartoes")
