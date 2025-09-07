from django.contrib import admin

from .models import Categoria, ContaBancaria, Transacao


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ("nome", "saldo_inicial")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nome",)


@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "categoria", "valor", "data", "tipo", "data_pagamento")
    list_filter = ("tipo", "data_pagamento", "data", "categoria")
