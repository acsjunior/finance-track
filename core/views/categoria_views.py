from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms.categoria_forms import CategoriaForm
from ..models import Categoria


def listar_categorias(request):
    categorias = Categoria.objects.all().order_by("nome")
    return render(
        request, "core/categorias/listar_categorias.html", {"categorias": categorias}
    )


def criar_categoria(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria criada com sucesso!")
            return redirect("categorias:listar_categorias")
        else:
            messages.error(request, "Erro ao criar categoria. Verifique os dados.")
    else:
        form = CategoriaForm()
    return render(
        request, "core/categorias/categoria_form.html", {"form": form, "acao": "Criar"}
    )


def editar_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada com sucesso!")
            return redirect("categorias:listar_categorias")
        else:
            messages.error(request, "Erro ao atualizar categoria. Verifique os dados.")
    else:
        form = CategoriaForm(instance=categoria)
    return render(
        request,
        "core/categorias/categoria_form.html",
        {"form": form, "categoria": categoria, "acao": "Editar"},
    )


@require_POST
def excluir_categoria(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    try:
        categoria.delete()
        messages.success(request, "Categoria excluída com sucesso!")
    except Exception:
        messages.error(
            request,
            "Não foi possível excluir a categoria. Existem transações vinculadas a ela.",
        )
    return redirect("categorias:listar_categorias")
