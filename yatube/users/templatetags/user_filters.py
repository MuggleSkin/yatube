from django import template
from django.template.defaultfilters import stringfilter

# В template.Library зарегистрированы все теги и фильтры шаблонов
# добавляем к ним и наш фильтр
register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={"class": css})


@register.filter(is_safe=False)
@stringfilter
def rupluralize(value, forms):
    """
    Подбирает окончание существительному после числа
    {{someval|rupluralize:"товар,товара,товаров"}}
    """
    try:
        one, two, many = forms.split(u",")

        value_mod_100 = int(value) % 100
        value_mod_10 = int(value) % 10

        if 21 > value_mod_100 > 4:
            return many

        if value_mod_10 == 1:
            return one
        elif value_mod_10 in (2, 3, 4):
            return two
        else:
            return many

    except (ValueError, TypeError):
        return many
