from decimal import Decimal

from django import template
from django.urls import reverse

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, "")


@register.simple_tag(takes_context=False)
def dynamic_url(url_name, obj, action_dict):
    param_name = action_dict.get("pk_field")
    param_value = obj.pk

    if not param_name:
        return "#"

    kwargs = {param_name: param_value}

    try:
        return reverse(url_name, kwargs=kwargs)
    except Exception as e:
        print(f"Erro ao gerar URL dinâmica para '{url_name}' com kwargs {kwargs}: {e}")
        return "#"


@register.filter
def status_badge(fatura):
    if fatura.paga:
        return '<span class="badge bg-success">Paga</span>'
    else:
        return '<span class="badge bg-danger">Pendente</span>'


@register.filter
def format_dinheiro_sinal(valor):
    if valor is None:
        return ""

    valor_decimal = Decimal(valor)

    if valor_decimal < 0:
        display_valor = f"- R$ {abs(valor_decimal):.2f}".replace(".", ",")
        css_class = "text-danger"
    else:
        display_valor = f"+ R$ {valor_decimal:.2f}".replace(".", ",")
        css_class = "text-success"

    return f'<span class="{css_class}">{display_valor}</span>'
