from django.contrib import admin

from .models import (
    CartaoCredito,
    Categoria,
    CompraParcelada,
    ContaBancaria,
    Fatura,
    Transacao,
    TransacaoCartao,
)


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


@admin.register(CartaoCredito)
class CartaoCreditoAdmin(admin.ModelAdmin):
    list_display = ("nome", "limite", "dia_fechamento", "dia_vencimento")


@admin.register(Fatura)
class FaturaAdmin(admin.ModelAdmin):
    list_display = (
        "cartao",
        "mes_referencia",
        "data_vencimento",
        "valor_total",
        "paga",
    )
    list_filter = ("cartao", "paga")


@admin.register(TransacaoCartao)
class TransacaoCartaoAdmin(admin.ModelAdmin):
    list_display = ("descricao", "fatura", "valor", "data")
    list_filter = ("fatura",)


@admin.register(CompraParcelada)
class CompraParceladaAdmin(admin.ModelAdmin):
    list_display = (
        "descricao",
        "cartao",
        "valor_total",
        "numero_parcelas",
        "data_compra",
    )
    list_filter = ("cartao", "data_compra")
