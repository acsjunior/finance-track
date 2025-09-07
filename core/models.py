from django.db import models


class ContaBancaria(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome da Conta")
    saldo_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Contas Bancárias"


class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Categorias"


class Transacao(models.Model):
    TIPO_CHOICES = (
        ("E", "Entrada"),
        ("S", "Saída"),
    )

    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data = models.DateField(verbose_name="Data de Vencimento")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES)
    data_pagamento = models.DateField(
        null=True, blank=True, verbose_name="Data do Pagamento"
    )
    conta = models.ForeignKey(
        ContaBancaria,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Conta",
    )

    def __str__(self):
        return f"{self.descricao} - R$ {self.valor}"

    class Meta:
        ordering = ["-data"]
        verbose_name = "Transação"
        verbose_name_plural = "Transações"
