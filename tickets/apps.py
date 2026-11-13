from django.apps import AppConfig


class TicketsConfig(AppConfig):
    name = 'tickets'

    def ready(self):
        from . import attachment_signals  # noqa: F401
