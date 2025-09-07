import json
from datetime import date

from dateutil.relativedelta import relativedelta
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .forms import DespesaForm, ReceitaForm, TransacaoForm  # Importe os novos forms
from .models import Categoria, Transacao


def dashboard(request):
    # --- 1. DETERMINAR O MÊS A SER EXIBIDO ---
    mes_str = request.GET.get("mes")
    hoje = date.today()

    if mes_str:
        try:
            ano, mes = map(int, mes_str.split("-"))
            mes_selecionado = date(ano, mes, 1)
        except:
            mes_selecionado = hoje.replace(day=1)
    else:
        mes_selecionado = hoje.replace(day=1)

    # --- 2. CALCULAR MÊS ANTERIOR E PRÓXIMO PARA PAGINAÇÃO ---
    mes_anterior = mes_selecionado - relativedelta(months=1)
    mes_seguinte = mes_selecionado + relativedelta(months=1)

    # --- 3. LÓGICA DE FORMULÁRIOS (POST) ---
    receita_form = ReceitaForm()
    despesa_form = DespesaForm()

    if request.method == "POST":
        if "submit_receita" in request.POST:
            receita_form = ReceitaForm(request.POST)
            if receita_form.is_valid():
                receita_form.save()
                return redirect(
                    f"{request.path}?mes={mes_selecionado.strftime('%Y-%m')}"
                )
        elif "submit_despesa" in request.POST:
            despesa_form = DespesaForm(request.POST)
            if despesa_form.is_valid():
                despesa_form.save()
                return redirect(
                    f"{request.path}?mes={mes_selecionado.strftime('%Y-%m')}"
                )

    # --- 4. FILTRAR DADOS E FAZER CÁLCULOS PARA O MÊS SELECIONADO ---
    entradas_do_mes = Transacao.objects.filter(
        data_pagamento__year=mes_selecionado.year,
        data_pagamento__month=mes_selecionado.month,
        tipo="E",
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))[
        "total"
    ]

    saidas_do_mes = Transacao.objects.filter(
        data_pagamento__year=mes_selecionado.year,
        data_pagamento__month=mes_selecionado.month,
        tipo="S",
    ).aggregate(total=Coalesce(Sum("valor"), Value(0), output_field=DecimalField()))[
        "total"
    ]

    balanco_do_mes = entradas_do_mes - saidas_do_mes

    despesas_pendentes = Transacao.objects.filter(
        data__year=mes_selecionado.year,
        data__month=mes_selecionado.month,
        tipo="S",
        data_pagamento__isnull=True,
    ).order_by("data")

    transacoes_do_mes = Transacao.objects.filter(
        data__year=mes_selecionado.year, data__month=mes_selecionado.month
    ).order_by("data")

    # --- 5. ENVIAR DADOS PARA O TEMPLATE ---
    context = {
        "balanco_do_mes": balanco_do_mes,
        "despesas_pendentes": despesas_pendentes,
        "transacoes_do_mes": transacoes_do_mes,
        "mes_selecionado": mes_selecionado,
        "mes_anterior": mes_anterior,
        "mes_seguinte": mes_seguinte,
        "receita_form": receita_form,
        "despesa_form": despesa_form,
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
