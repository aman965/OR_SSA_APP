import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.orsaas_backend.settings')
django.setup()

from backend.core.models import Scenario

updated = Scenario.objects.all().update(status='created')
print(f'Reset {updated} scenarios to "created" status')
