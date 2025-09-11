from django.contrib import messages
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

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
    Categoria,
    Fatura,
    Transacao,
)
from .transacao_cartao_views import processar_lancamento_cartao


def listar_faturas(request, cartao_pk):
    cartao = get_object_or_404(CartaoCredito, pk=cartao_pk)

    if request.method == "POST":
        form_processado, _ = processar_lancamento_cartao(request, cartao)

        if "submit_despesa_cartao" in request.POST:
            despesa_form = form_processado
        else:
            receita_form = form_processado

        if form_processado.is_valid():
            return redirect("listar_faturas", cartao_pk=cartao.pk)

    else:
        despesa_form = DespesaCartaoForm(cartao=cartao)
        receita_form = ReceitaCartaoForm(cartao=cartao)

    faturas = (
        Fatura.objects.filter(cartao=cartao)
        .annotate(
            soma_transacoes=Coalesce(
                Sum("transacoes__valor"), Value(0), output_field=DecimalField()
            )
        )
        .order_by("-mes_referencia")
    )

    for fatura in faturas:
        if fatura.valor_total != fatura.soma_transacoes:
            fatura.valor_total = fatura.soma_transacoes
            fatura.save()

    context = {
        "cartao": cartao,
        "faturas": faturas,
        "despesa_form": despesa_form,
        "receita_form": receita_form,
        "form_action": reverse(
            "cartoes:listar_faturas", kwargs={"cartao_pk": cartao.pk}
        ),
    }
    return render(request, "core/cartoes/faturas/listar_faturas.html", context)


def detalhe_fatura(request, fatura_pk):
    fatura = get_object_or_404(Fatura, pk=fatura_pk)
    cartao = fatura.cartao

    if request.method == "POST":
        form_processado, fatura_impactada = processar_lancamento_cartao(request, cartao)

        if form_processado.is_valid():
            return redirect("detalhe_fatura", fatura_pk=fatura_impactada.pk)

        despesa_form = (
            form_processado
            if "submit_despesa_cartao" in request.POST
            else DespesaCartaoForm(cartao=cartao)
        )
        receita_form = (
            form_processado
            if "submit_receita_cartao" in request.POST
            else ReceitaCartaoForm(cartao=cartao)
        )

    else:
        despesa_form = DespesaCartaoForm(cartao=cartao)
        receita_form = ReceitaCartaoForm(cartao=cartao)

    despesas = fatura.transacoes.all().order_by("-data")

    total_fatura = despesas.aggregate(
        soma=Coalesce(Sum("valor"), Value(0), output_field=DecimalField())
    )["soma"]
    if fatura.valor_total != total_fatura:
        fatura.valor_total = total_fatura
        fatura.save()

    context = {
        "fatura": fatura,
        "cartao": cartao,
        "despesas": despesas,
        "despesa_form": despesa_form,
        "receita_form": receita_form,
        "form_action": reverse("detalhe_fatura", args=[fatura.pk]),
    }
    return render(request, "core/cartoes/faturas/detalhe_fatura.html", context)


def editar_fatura(request, fatura_pk):
    fatura = get_object_or_404(Fatura, pk=fatura_pk)
    if request.method == "POST":
        form = FaturaForm(request.POST, instance=fatura)
        if form.is_valid():
            form.save()
            return redirect("listar_faturas", cartao_pk=fatura.cartao.pk)
    else:
        form = FaturaForm(instance=fatura)
    return render(
        request,
        "core/cartoes/faturas/fatura_form.html",
        {"form": form, "fatura": fatura},
    )


def pagar_fatura(request, fatura_pk):
    fatura = get_object_or_404(Fatura, pk=fatura_pk)

    if request.method == "POST":
        form = PagamentoFaturaForm(request.POST)
        if form.is_valid():
            conta_pagamento = form.cleaned_data["conta"]
            data_do_pagamento = form.cleaned_data["data_pagamento"]
            categoria_cartao, created = Categoria.objects.get_or_create(
                nome="Cartão de Crédito"
            )

            transacao = Transacao.objects.create(
                descricao=f"Pagamento Fatura {fatura.cartao.nome} ({fatura.mes_referencia.strftime('%b/%Y')})",
                valor=fatura.valor_total,
                data=data_do_pagamento,
                data_pagamento=data_do_pagamento,
                categoria=categoria_cartao,
                tipo="S",
                conta=conta_pagamento,
            )

            fatura.paga = True
            fatura.transacao_pagamento = transacao
            fatura.save()

            messages.success(
                request, f"Fatura de {fatura.cartao.nome} paga com sucesso!"
            )
            return redirect("detalhe_fatura", fatura_pk=fatura.pk)
    else:
        form = PagamentoFaturaForm()

    context = {
        "fatura": fatura,
        "form": form,
    }
    return render(request, "core/cartoes/faturas/pagar_fatura.html", context)
