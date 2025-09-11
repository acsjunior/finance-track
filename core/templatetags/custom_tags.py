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
