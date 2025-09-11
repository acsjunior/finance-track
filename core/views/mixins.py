from django.urls import reverse_lazy


class FormContextMixin:
    acao = None
    cancel_url_name = ""
    titulo = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.acao is None:
            if hasattr(self, "object") and self.object:
                context["acao"] = "Editar"
            else:
                context["acao"] = "Criar"
        else:
            context["acao"] = self.acao

        context["cancel_url"] = getattr(self, "cancel_url_name", None)
        context["titulo"] = self.titulo or context["acao"]

        return context


class ListContextMixin:
    object_list_name = None
    headers = []
    fields = []
    criar_url_name = None
    criar_label = None
    titulo = None
    editar_url_name = None
    excluir_url_name = None
    empty_message = None
    row_actions = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for attr in [
            "headers",
            "fields",
            "criar_label",
            "titulo",
            "editar_url_name",
            "excluir_url_name",
            "empty_message",
            "row_actions",
        ]:
            value = getattr(self, attr, None)
            if value is not None:
                context[attr] = value

        if getattr(self, "criar_url_name", None):
            context["criar_url"] = reverse_lazy(self.criar_url_name)

        if self.object_list_name:
            context[self.object_list_name] = context.get("object_list")

        return context
