from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from ..forms.transacao_cartao_forms import (
    DespesaCartaoForm,
    ReceitaCartaoForm,
)
from ..models import CartaoCredito, CompraParcelada, TransacaoCartao
from ..utils import get_fatura_aberta


def processar_lancamento_cartao(request, cartao):
    form = None
    fatura_impactada = None
    is_despesa = "submit_despesa_cartao" in request.POST

    if is_despesa:
        form = DespesaCartaoForm(request.POST, cartao=cartao)
    else:
        form = ReceitaCartaoForm(request.POST, cartao=cartao)

    if form.is_valid():
        numero_parcelas = form.cleaned_data.get("numero_parcelas", 1)
        valor_total = form.cleaned_data["valor"]
        data_compra = form.cleaned_data["data"]
        descricao_original = form.cleaned_data["descricao"]
        categoria = form.cleaned_data["categoria"]

        compra_mae = CompraParcelada.objects.create(
            cartao=cartao,
            descricao=descricao_original,
            valor_total=valor_total,
            numero_parcelas=numero_parcelas,
            data_compra=data_compra,
        )

        valor_parcela = round(valor_total / Decimal(numero_parcelas), 2)

        soma_parcelas = valor_parcela * (numero_parcelas - 1)
        ultima_parcela = valor_total - soma_parcelas

        for i in range(numero_parcelas):
            data_parcela_ref = data_compra + relativedelta(months=i)
            fatura_parcela = get_fatura_aberta(cartao, data_parcela_ref)
            fatura_impactada = fatura_parcela

            valor_desta_parcela = (
                valor_parcela if i < numero_parcelas - 1 else ultima_parcela
            )

            TransacaoCartao.objects.create(
                fatura=fatura_parcela,
                descricao=f"{descricao_original} ({i + 1}/{numero_parcelas})",
                valor=valor_desta_parcela if is_despesa else -valor_desta_parcela,
                categoria=categoria,
                data=data_compra,
                compra_parcelada=compra_mae,
            )

        messages.success(request, "Lançamento registrado com sucesso!")
    else:
        messages.error(request, "Por favor, corrija os erros no formulário.")

    return form, fatura_impactada


def lancar_transacao_cartao(request, pk):
    cartao = get_object_or_404(CartaoCredito, pk=pk)
    if request.method == "POST":
        form = None
        is_despesa = "submit_despesa_cartao" in request.POST
        if is_despesa:
            form = DespesaCartaoForm(request.POST, cartao=cartao)
        else:
            form = ReceitaCartaoForm(request.POST, cartao=cartao)

        if form and form.is_valid():
            numero_parcelas = form.cleaned_data.get("numero_parcelas", 1)
            valor_total = form.cleaned_data["valor"]
            data_compra = form.cleaned_data["data"]
            descricao_original = form.cleaned_data["descricao"]
            categoria = form.cleaned_data["categoria"]

            compra_mae = CompraParcelada.objects.create(
                cartao=cartao,
                descricao=descricao_original,
                valor_total=valor_total,
                numero_parcelas=numero_parcelas,
                data_compra=data_compra,
            )

            valor_parcela = round(valor_total / Decimal(numero_parcelas), 2)

            for i in range(numero_parcelas):
                data_parcela_ref = data_compra + relativedelta(months=i)
                fatura_parcela = get_fatura_aberta(cartao, data_parcela_ref)

                TransacaoCartao.objects.create(
                    fatura=fatura_parcela,
                    descricao=f"{descricao_original} ({i + 1}/{numero_parcelas})",
                    valor=valor_parcela if is_despesa else -valor_parcela,
                    categoria=categoria,
                    data=data_compra,
                    compra_parcelada=compra_mae,
                )

            messages.success(request, "Lançamento registrado com sucesso!")
            return redirect("listar_faturas", cartao_pk=cartao.pk)
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
            context = {
                "cartao": cartao,
                "despesa_form": form
                if is_despesa
                else DespesaCartaoForm(cartao=cartao),
                "receita_form": form
                if not is_despesa
                else ReceitaCartaoForm(cartao=cartao),
            }
            return render(request, "core/lancar_transacao_cartao.html", context)

    else:
        despesa_form = DespesaCartaoForm(cartao=cartao)
        receita_form = ReceitaCartaoForm(cartao=cartao)
        context = {
            "cartao": cartao,
            "despesa_form": despesa_form,
            "receita_form": receita_form,
        }
        return render(request, "core/lancar_transacao_cartao.html", context)


def editar_transacao_cartao(request, pk):
    transacao = get_object_or_404(TransacaoCartao, pk=pk)

    redirect_to_fatura_detail = reverse("detalhe_fatura", args=[transacao.fatura.pk])

    FormClass = DespesaCartaoForm if transacao.valor >= 0 else ReceitaCartaoForm

    if request.method == "POST":
        form = FormClass(
            request.POST, instance=transacao, cartao=transacao.fatura.cartao
        )

        if form.is_valid():
            valor_digitado_no_form = form.cleaned_data["valor"]

            if transacao.valor >= 0:
                transacao.valor = valor_digitado_no_form
            else:
                transacao.valor = -valor_digitado_no_form

            form.save()

            fatura_a_atualizar = transacao.fatura
            total_transacoes = TransacaoCartao.objects.filter(
                fatura=fatura_a_atualizar
            ).aggregate(
                soma=Coalesce(Sum("valor"), Value(0), output_field=DecimalField())
            )["soma"]

            if fatura_a_atualizar.paga and fatura_a_atualizar.transacao_pagamento:
                transacao_pagamento = fatura_a_atualizar.transacao_pagamento
                transacao_pagamento.valor = total_transacoes
                transacao_pagamento.save()

            fatura_a_atualizar.valor_total = total_transacoes
            fatura_a_atualizar.save()

            messages.success(request, "Transação de cartão editada com sucesso!")
            return redirect(redirect_to_fatura_detail)
        else:
            messages.error(
                request, "Erro ao editar transação. Por favor, corrija os campos."
            )

    else:
        initial_value_for_form = abs(transacao.valor)

        form = FormClass(
            instance=transacao,
            cartao=transacao.fatura.cartao,
            initial={"valor": initial_value_for_form},
        )

        if transacao.compra_parcelada:
            if "numero_parcelas" in form.fields:
                form.fields["numero_parcelas"].widget.attrs["readonly"] = True
                form.fields[
                    "numero_parcelas"
                ].help_text = (
                    "Edite a compra parcelada mãe para alterar o número de parcelas."
                )

    context = {
        "form": form,
        "transacao": transacao,
        "fatura": transacao.fatura,
        "form_action": reverse("editar_transacao_cartao", args=[transacao.pk]),
    }
    return render(request, "core/editar_transacao_cartao.html", context)


@require_POST
def excluir_transacao_cartao(request, pk):
    transacao = get_object_or_404(TransacaoCartao, pk=pk)
    fatura = transacao.fatura

    transacao.delete()

    total_transacoes = TransacaoCartao.objects.filter(fatura=fatura).aggregate(
        soma=Coalesce(Sum("valor"), Value(0), output_field=DecimalField())
    )["soma"]
    fatura.valor_total = total_transacoes
    fatura.save()

    messages.success(request, "Transação de cartão excluída com sucesso!")
    return redirect("detalhe_fatura", fatura_pk=fatura.pk)
