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
    icone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Classe CSS do ícone (ex: bi bi-house, bi bi-car). Consulte Bootstrap Icons.",
    )

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
        on_delete=models.SET_NULL,
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


class CartaoCredito(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome do Cartão")
    limite = models.DecimalField(max_digits=10, decimal_places=2)
    dia_fechamento = models.PositiveIntegerField(
        verbose_name="Dia do Fechamento da Fatura"
    )
    dia_vencimento = models.PositiveIntegerField(
        verbose_name="Dia do Vencimento da Fatura"
    )

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name_plural = "Cartões de Crédito"


class Fatura(models.Model):
    cartao = models.ForeignKey(
        CartaoCredito, on_delete=models.CASCADE, related_name="faturas"
    )
    mes_referencia = models.DateField(verbose_name="Mês de Referência")
    data_fechamento = models.DateField()
    data_vencimento = models.DateField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paga = models.BooleanField(default=False)

    # Esta transação será a "ponte" com o dashboard principal
    transacao_pagamento = models.OneToOneField(
        Transacao, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"Fatura de {self.cartao.nome} - {self.mes_referencia.strftime('%B/%Y')}"

    class Meta:
        # Garante que só existe uma fatura por cartão para um determinado mês
        unique_together = ("cartao", "mes_referencia")


class CompraParcelada(models.Model):
    cartao = models.ForeignKey(CartaoCredito, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=200)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    numero_parcelas = models.PositiveIntegerField()
    data_compra = models.DateField()

    def __str__(self):
        return f"{self.descricao} ({self.numero_parcelas}x)"


class TransacaoCartao(models.Model):
    fatura = models.ForeignKey(
        Fatura, on_delete=models.CASCADE, related_name="transacoes"
    )
    descricao = models.CharField(max_length=200)
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Use um valor negativo para estornos"
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, blank=True
    )
    data = models.DateField(verbose_name="Data da Compra")

    compra_parcelada = models.ForeignKey(
        CompraParcelada, on_delete=models.CASCADE, related_name="parcelas"
    )

    def __str__(self):
        return self.descricao

    class Meta:
        verbose_name = "Transação de Cartão"
        verbose_name_plural = "Transações de Cartão"
