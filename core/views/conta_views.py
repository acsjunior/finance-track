from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import ContaBancariaForm
from ..models import ContaBancaria


def listar_contas(request):
    contas = ContaBancaria.objects.all()
    return render(request, "core/contas/listar_contas.html", {"contas": contas})


def criar_conta(request):
    if request.method == "POST":
        form = ContaBancariaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("contas:listar_contas")
    else:
        form = ContaBancariaForm()
    return render(
        request,
        "core/contas/conta_form.html",
        {"form": form, "titulo": "Criar Nova Conta"},
    )


def editar_conta(request, pk):
    conta = get_object_or_404(ContaBancaria, pk=pk)
    if request.method == "POST":
        form = ContaBancariaForm(request.POST, instance=conta)
        if form.is_valid():
            form.save()
            return redirect("contas:listar_contas")
    else:
        form = ContaBancariaForm(instance=conta)
    return render(
        request, "core/contas/conta_form.html", {"form": form, "titulo": "Editar Conta"}
    )


@require_POST
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
    return redirect("contas:listar_contas")
