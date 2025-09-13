from django.contrib import messages
from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)


class GenericListView(ListView):
    template_name = ""
    context_object_name = "objects"
    ordering = None

    def get_queryset(self):
        queryset = self.model.objects.all()
        if self.ordering:
            queryset = queryset.order_by(*self.ordering)
        return queryset


class GenericCreateView(CreateView):
    template_name = ""
    success_url = None

    def form_valid(self, form):
        messages.success(self.request, f"{self.model.__name__} criado com sucesso!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, f"Erro ao criar {self.model.__name__}.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["acao"] = "Criar"
        return context


class GenericUpdateView(UpdateView):
    template_name = ""
    success_url = None

    def form_valid(self, form):
        messages.success(self.request, f"{self.model.__name__} atualizado com sucesso!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, f"Erro ao atualizar {self.model.__name__}.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["acao"] = "Editar"
        return context


class GenericDeleteView(DeleteView):
    success_url = None

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, f"{self.model.__name__} excluído com sucesso!")
        except Exception:
            messages.error(
                request,
                f"Não foi possível excluir {self.model.__name__}. "
                f"Ele pode estar vinculado a outros registros.",
            )
        return redirect(self.success_url)


class GenericDetailView(DetailView):
    template_name = ""
    context_object_name = "object"
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model_name = getattr(
            self.model._meta, "verbose_name", self.model.__name__
        ).capitalize()
        context["titulo"] = f"Detalhes do {model_name}"
        return context
