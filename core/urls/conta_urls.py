from django.urls import path

from ..views.conta_views import criar_conta, editar_conta, excluir_conta, listar_contas

app_name = "contas"

urlpatterns = [
    path("", listar_contas, name="listar_contas"),
    path("nova/", criar_conta, name="criar_conta"),
    path("<int:pk>/editar/", editar_conta, name="editar_conta"),
    path("<int:pk>/excluir/", excluir_conta, name="excluir_conta"),
]
