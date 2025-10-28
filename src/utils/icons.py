# src/utils/icons.py
def icon_model(model):
    return {
        'dataset': '🧠',
        'dashboard': '📊',
        'card': '📄',
        'metric': '📏',
        'pulse': '🔔',
        'timeline': '📆',
    }.get(model, '📄')


def icon_display(display_type):
    return {
        'scalar': '🔢',
        'bar': '📊',
        'line': '📈',
        'table': '🧮',
        'pie': '🥧',
        'map': '🗺️',
    }.get(display_type, '📄')

def icon_bool(val):
    return '✅' if val else '❌'