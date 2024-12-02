from django import template
from datetime import datetime

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def to_datetime(value, format="%Y-%m-%dT%H:%M:%S"):
    return datetime.strptime(value, format)