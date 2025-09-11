import calendar
from datetime import date

from dateutil.relativedelta import relativedelta


def get_safe_day_in_month(year, month, day):
    ultimo_dia_do_mes = calendar.monthrange(year, month)[1]
    dia_seguro = min(day, ultimo_dia_do_mes)
    return date(year, month, dia_seguro)


def get_fatura_aberta(cartao, data_compra):
    data_fechamento_neste_mes = get_safe_day_in_month(
        data_compra.year, data_compra.month, cartao.dia_fechamento
    )

    if data_compra > data_fechamento_neste_mes:
        mes_referencia = data_compra + relativedelta(months=1)
    else:
        mes_referencia = data_compra

    mes_referencia = mes_referencia.replace(day=1)

    data_fechamento_calculada = get_safe_day_in_month(
        mes_referencia.year, mes_referencia.month, cartao.dia_fechamento
    )

    data_vencimento_referencia = mes_referencia + relativedelta(months=1)
    data_vencimento_calculada = get_safe_day_in_month(
        data_vencimento_referencia.year,
        data_vencimento_referencia.month,
        cartao.dia_vencimento,
    )

    fatura, created = Fatura.objects.get_or_create(
        cartao=cartao,
        mes_referencia=mes_referencia,
        defaults={
            "data_fechamento": data_fechamento_calculada,
            "data_vencimento": data_vencimento_calculada,
        },
    )

    return fatura
