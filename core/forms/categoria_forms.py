from django import forms

from ..models import Categoria


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nome", "icone"]
        widgets = {
            "nome": forms.TextInput(attrs={"class": "form-control"}),
            "icone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ex: bi bi-house"}
            ),
        }
        labels = {
            "nome": "Nome da Categoria",
            "icone": "Ícone",
        }
        help_texts = {
            "icone": "Use classes do Bootstrap Icons (ex: bi bi-house).",
        }
