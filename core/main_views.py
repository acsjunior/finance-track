import calendar
import json
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .main_forms import (
    DespesaCartaoForm,
    DespesaForm,
    FaturaForm,
    PagamentoFaturaForm,
    ReceitaCartaoForm,
    ReceitaForm,
    TransacaoForm,
)
from .models import (
    CartaoCredito,
    Categoria,
    CompraParcelada,
    ContaBancaria,
    Fatura,
    Transacao,
    TransacaoCartao,
)


def dashboard(request):
    # --- 1. FILTRAGEM DE CONTA E MÊS ---
    contas = ContaBancaria.objects.all()
    conta_selecionada_id = request.GET.get("conta")

    transacoes = Transacao.objects.all()
    contas_a_calcular = contas

    if conta_selecionada_id:
        try:
            conta_selecionada_id = int(conta_selecionada_id)
            transacoes = transacoes.filter(conta_id=conta_selecionada_id)
            contas_a_calcular = contas.filter(id=conta_selecionada_id)
        except (ValueError, TypeError):
            conta_selecionada_id = None

    # Lógica de paginação por mês
    mes_str = request.GET.get("mes")
    hoje = date.today()
    if mes_str:
        try:
            ano, mes = map(int, mes_str.split("-"))
            mes_selecionado = date(ano, mes, 1)
        except (ValueError, TypeError):
            mes_selecionado = hoje.replace(day=1)
    else:
        mes_selecionado = hoje.replace(day=1)

    mes_anterior = mes_selecionado - relativedelta(months=1)
    mes_seguinte = mes_selecionado + relativedelta(months=1)

    # --- 2. CÁLCULO DO SALDO INICIAL DO MÊS ---
    # Soma o saldo inicial das contas a serem consideradas (pode ser uma ou todas)
    saldo_inicial_contas = contas_a_calcular.aggregate(
        total=Coalesce(Sum("saldo_inicial"), Value(0), output_field=DecimalField())
    )["total"]

    # Soma todas as transações pagas ANTES do mês selecionado
    entradas_passadas = transacoes.filter(
        data_pagamento__lt=mes_selecionado, tipo="E"
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))[
        "total"
    ]

    saidas_passadas = transacoes.filter(
        data_pagamento__lt=mes_selecionado, tipo="S"
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))[
        "total"
    ]

    saldo_inicial_do_mes = saldo_inicial_contas + entradas_passadas - saidas_passadas

    # --- 3. CÁLCULOS DENTRO DO MÊS SELECIONADO ---
    entradas_do_mes = transacoes.filter(
        data_pagamento__year=mes_selecionado.year,
        data_pagamento__month=mes_selecionado.month,
        tipo="E",
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))[
        "total"
    ]

    saidas_do_mes = transacoes.filter(
        data_pagamento__year=mes_selecionado.year,
        data_pagamento__month=mes_selecionado.month,
        tipo="S",
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))[
        "total"
    ]

    saldo_final_do_mes = saldo_inicial_do_mes + entradas_do_mes - saidas_do_mes

    despesas_pendentes = transacoes.filter(
        data__year=mes_selecionado.year,
        data__month=mes_selecionado.month,
        tipo="S",
        data_pagamento__isnull=True,
    ).order_by("data")

    transacoes_do_mes = Transacao.objects.filter(
        data__year=mes_selecionado.year, data__month=mes_selecionado.month
    ).order_by("data")
    if conta_selecionada_id:
        transacoes_do_mes = transacoes_do_mes.filter(conta_id=conta_selecionada_id)

    faturas_abertas_do_mes = Fatura.objects.filter(
        data_vencimento__year=mes_selecionado.year,
        data_vencimento__month=mes_selecionado.month,
        paga=False,
    ).annotate(
        soma_despesas=Coalesce(
            Sum("transacoes__valor"),
            Value(0),
            output_field=DecimalField(),  # <-- CORREÇÃO AQUI
        )
    )

    # --- 4. LÓGICA DE FORMULÁRIOS (POST) ---
    receita_form = ReceitaForm()
    despesa_form = DespesaForm()
    if request.method == "POST":
        redirect_url = f"{request.path}?mes={mes_selecionado.strftime('%Y-%m')}"
        if conta_selecionada_id:
            redirect_url += f"&conta={conta_selecionada_id}"

        if "submit_receita" in request.POST:
            receita_form = ReceitaForm(request.POST)
            if receita_form.is_valid():
                receita_form.save()
                return redirect(redirect_url)
        elif "submit_despesa" in request.POST:
            despesa_form = DespesaForm(request.POST)
            if despesa_form.is_valid():
                despesa_form.save()
                return redirect(redirect_url)

    # --- 5. CONTEXTO PARA O TEMPLATE ---
    context = {
        "saldo_final_do_mes": saldo_final_do_mes,
        "despesas_pendentes": despesas_pendentes,
        "transacoes_do_mes": transacoes_do_mes,
        "mes_selecionado": mes_selecionado,
        "mes_anterior": mes_anterior,
        "mes_seguinte": mes_seguinte,
        "receita_form": receita_form,
        "despesa_form": despesa_form,
        "contas": contas,
        "conta_selecionada_id": conta_selecionada_id,
        "faturas_abertas_do_mes": faturas_abertas_do_mes,
    }

    return render(request, "core/dashboard.html", context)


@csrf_exempt
def adicionar_categoria_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nome_categoria = data.get("nome")

            if nome_categoria:
                nova_categoria = Categoria.objects.create(nome=nome_categoria)
                return JsonResponse(
                    {
                        "status": "success",
                        "id": nova_categoria.id,
                        "nome": nova_categoria.nome,
                    }
                )
            else:
                return JsonResponse(
                    {"status": "error", "message": "Nome da categoria não fornecido."},
                    status=400,
                )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Dados JSON inválidos."}, status=400
            )

    return JsonResponse(
        {"status": "error", "message": "Método não permitido."}, status=405
    )


def excluir_transacao(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk)
    transacao.delete()
    return redirect("dashboard")


def editar_transacao(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk)

    if request.method == "POST":
        form = TransacaoForm(request.POST, instance=transacao)
        if form.is_valid():
            form.save()
            return redirect("dashboard")
    else:
        form = TransacaoForm(instance=transacao)

    return render(
        request, "core/editar_transacao.html", {"form": form, "transacao": transacao}
    )


def get_safe_day_in_month(year, month, day):
    ultimo_dia_do_mes = calendar.monthrange(year, month)[1]
    dia_seguro = min(day, ultimo_dia_do_mes)
    return date(year, month, dia_seguro)


def get_fatura_aberta(cartao, data_compra):
    data_fechamento_neste_mes = get_safe_day_in_month(
        data_compra.year, data_compra.month, cartao.dia_fechamento
    )

    if data_compra > data_fechamento_neste_mes:
        mes_referencia = data_compra + relativedelta(months=1)
    else:
        mes_referencia = data_compra

    mes_referencia = mes_referencia.replace(day=1)

    data_fechamento_calculada = get_safe_day_in_month(
        mes_referencia.year, mes_referencia.month, cartao.dia_fechamento
    )

    data_vencimento_referencia = mes_referencia + relativedelta(months=1)
    data_vencimento_calculada = get_safe_day_in_month(
        data_vencimento_referencia.year,
        data_vencimento_referencia.month,
        cartao.dia_vencimento,
    )

    fatura, created = Fatura.objects.get_or_create(
        cartao=cartao,
        mes_referencia=mes_referencia,
        defaults={
            "data_fechamento": data_fechamento_calculada,
            "data_vencimento": data_vencimento_calculada,
        },
    )

    return fatura


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
        "form_action": reverse("listar_faturas", args=[cartao.pk]),
    }
    return render(request, "core/listar_faturas.html", context)


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
    return render(request, "core/detalhe_fatura.html", context)


def editar_fatura(request, fatura_pk):
    fatura = get_object_or_404(Fatura, pk=fatura_pk)
    if request.method == "POST":
        form = FaturaForm(request.POST, instance=fatura)
        if form.is_valid():
            form.save()
            return redirect("listar_faturas", cartao_pk=fatura.cartao.pk)
    else:
        form = FaturaForm(instance=fatura)
    return render(request, "core/fatura_form.html", {"form": form, "fatura": fatura})


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
    return render(request, "core/pagar_fatura.html", context)


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
