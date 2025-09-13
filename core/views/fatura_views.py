from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView
from django.views.generic.detail import SingleObjectMixin

from core.views.generic_crud import (
    GenericDetailView,
    GenericListView,
    GenericUpdateView,
)
from core.views.mixins import FormContextMixin, ListContextMixin

from ..forms.fatura_forms import (
    FaturaForm,
    PagamentoFaturaForm,
)
from ..forms.transacao_cartao_forms import (
    DespesaCartaoForm,
    ReceitaCartaoForm,
)
from ..models import (
    CartaoCredito,
    Fatura,
)
from .transacao_cartao_views import processar_lancamento_cartao


class FaturaListView(ListContextMixin, GenericListView):
    model = Fatura
    template_name = "core/cartoes/faturas/listar_faturas.html"
    context_object_name = "faturas"
    ordering = ["-mes_referencia"]
    empty_message = "Nenhuma fatura encontrada para este cartão."

    def get_cartao(self):
        return get_object_or_404(CartaoCredito, pk=self.kwargs["cartao_pk"])

    def get_despesa_form(self):
        return DespesaCartaoForm(cartao=self.get_cartao())

    def get_receita_form(self):
        return ReceitaCartaoForm(cartao=self.get_cartao())

    def get_queryset(self):
        cartao = self.get_cartao()
        return (
            super()
            .get_queryset()
            .filter(cartao=cartao)
            .annotate(
                soma_transacoes=Coalesce(
                    Sum("transacoes__valor"), Value(0), output_field=DecimalField()
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cartao = self.get_cartao()
        context.update(
            {
                "cartao": cartao,
                "titulo": f"Faturas de {cartao.nome}",
                "despesa_form": self.get_despesa_form(),
                "receita_form": self.get_receita_form(),
                "form_action": reverse(
                    "cartoes:lancar_transacao_cartao", kwargs={"cartao_pk": cartao.pk}
                ),
            }
        )
        return context


class FaturaDetailView(GenericDetailView):
    model = Fatura
    template_name = "core/cartoes/faturas/detalhe_fatura.html"
    context_object_name = "fatura"
    pk_url_kwarg = "fatura_pk"

    FORM_MAPPING = {
        "submit_despesa_cartao": "despesa_form",
        "submit_receita_cartao": "receita_form",
    }

    def get_cartao(self):
        return self.object.cartao

    def get_despesa_form(self):
        return DespesaCartaoForm(cartao=self.get_cartao())

    def get_receita_form(self):
        return ReceitaCartaoForm(cartao=self.get_cartao())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fatura = self.object
        cartao = self.get_cartao()

        fatura.atualizar_valor_total(save=False)

        context.update(
            {
                "cartao": cartao,
                "despesas": fatura.transacoes.all().order_by("-data"),
                "despesa_form": kwargs.get("despesa_form", self.get_despesa_form()),
                "receita_form": kwargs.get("receita_form", self.get_receita_form()),
                "total_fatura": fatura.valor_total,
                "titulo": "Detalhes da Fatura",
                "form_action": reverse(
                    "cartoes:detalhe_fatura", kwargs={"fatura_pk": fatura.pk}
                ),
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        cartao = self.get_cartao()
        form_processado, fatura_impactada = processar_lancamento_cartao(request, cartao)
        target_context_key = None

        for submit_key, context_key in self.FORM_MAPPING.items():
            if submit_key in request.POST:
                target_context_key = context_key
                break

        if form_processado.is_valid():
            return redirect("cartoes:detalhe_fatura", fatura_pk=fatura_impactada.pk)

        kwargs_context = (
            {target_context_key: form_processado} if target_context_key else {}
        )
        context = self.get_context_data(**kwargs_context)

        messages.error(
            request, "Erro ao processar o lançamento. Verifique os dados fornecidos."
        )
        return self.render_to_response(context)


class FaturaUpdateView(FormContextMixin, GenericUpdateView):
    model = Fatura
    form_class = FaturaForm
    template_name = "core/cartoes/faturas/fatura_form.html"

    @property
    def titulo(self):
        if self.object:
            return f"Editar Fatura {self.object.mes_referencia.strftime('%B/%Y')}"
        return "Editar Fatura"

    def get_success_url(self):
        return self.object.get_list_url()

    def get_cancel_url_name(self):
        return self.object.get_detail_url()


class FaturaPagarView(SingleObjectMixin, FormView):
    model = Fatura
    form_class = PagamentoFaturaForm
    template_name = "core/cartoes/faturas/pagar_fatura.html"
    pk_url_kwarg = "fatura_pk"

    def form_valid(self, form):
        fatura = self.object
        try:
            fatura.pagar(
                conta=form.cleaned_data["conta"],
                data_pagamento=form.cleaned_data["data_pagamento"],
            )
        except ValidationError as e:
            messages.error(self.request, e.message)
            return self.form_invalid(form)

        messages.success(
            self.request, f"Fatura de {fatura.cartao.nome} paga com sucesso!"
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Erro ao processar o pagamento da fatura. Verifique os dados fornecidos.",
        )
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if "from_list" in self.request.GET:
            return reverse_lazy(
                "cartoes:listar_faturas", kwargs={"cartao_pk": self.object.cartao.pk}
            )
        return reverse_lazy(
            "cartoes:detalhe_fatura", kwargs={"fatura_pk": self.object.pk}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fatura = self.get_object()
        context.update(
            {
                "fatura": fatura,
                "titulo": f"Pagar Fatura {fatura.mes_referencia.strftime('%B/%Y')}",
                "form_action": reverse(
                    "cartoes:pagar_fatura", kwargs={"fatura_pk": fatura.pk}
                ),
            }
        )
        return context
