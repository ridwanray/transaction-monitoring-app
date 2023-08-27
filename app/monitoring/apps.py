from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MonitoringConfig(AppConfig):
    name = 'monitoring'
    verbose_name = _('monitoring')
