from django.db.models import Q
from .models import EnvironmentSetting

def get_env_settings(setting_type):
    try:
        return list(
            EnvironmentSetting.objects.filter(setting_type=setting_type).values_list('value', flat=True)
        )
    except:
        return []  # Fallback if DB not ready (e.g., during collectstatic, migrations)
