"""OS-specific feature adapters (ADR-156).

Каждый модуль — набор adapter-классов для одной ОС.
Все возвращают "мягкий" результат: либо значение, либо None/False.
Graceful degradation (Nielsen 1993).
"""
