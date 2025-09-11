from django.urls import reverse_lazy

from core.views.generic_crud import (
    GenericCreateView,
    GenericDeleteView,
    GenericListView,
    GenericUpdateView,
)

from ..forms import CartaoCreditoForm
from ..models import CartaoCredito
from ..views.mixins import FormContextMixin, ListContextMixin


class CartaoListView(ListContextMixin, GenericListView):
    model = CartaoCredito
    template_name = "core/cartoes/listar_cartoes.html"
    context_object_name = "cartoes"
    ordering = ["nome"]
    titulo = "Meus Cartões de Crédito"
    criar_url_name = "cartoes:criar_cartao"
    criar_label = "Adicionar Novo Cartão"
    editar_url_name = "cartoes:editar_cartao"
    excluir_url_name = "cartoes:excluir_cartao"
    headers = ["Nome do Cartão", "Limite", "Dia do Fechamento", "Dia do Vencimento"]
    fields = ["nome", "limite", "dia_fechamento", "dia_vencimento"]
    empty_message = "Nenhum cartão de crédito cadastrado."


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
