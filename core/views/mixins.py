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
