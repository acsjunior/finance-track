import json
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .forms import (  # Importe os novos forms
    ContaBancariaForm,
    DespesaForm,
    ReceitaForm,
    TransacaoForm,
)
from .models import Categoria, ContaBancaria, Transacao


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


def listar_contas(request):
    contas = ContaBancaria.objects.all()
    return render(request, "core/listar_contas.html", {"contas": contas})


def criar_conta(request):
    if request.method == "POST":
        form = ContaBancariaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("listar_contas")
    else:
        form = ContaBancariaForm()
    return render(request, "core/conta_form.html", {"form": form})


def editar_conta(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk)
    if request.method == "POST":
        form = ContaBancariaForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
            return redirect("listar_contas")
    else:
        form = ContaBancariaForm(instance=conta)
    return render(request, "core/conta_form.html", {"form": form, "conta": conta})


def excluir_conta(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk)
    try:
        conta.delete()
        messages.success(request, "Conta excluída com sucesso.")
    except Exception:
        messages.error(
            request,
            "Não foi possível excluir a conta. Existem transações vinculadas a ela.",
        )
    return redirect("listar_contas")
