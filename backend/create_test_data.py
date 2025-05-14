import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()

from core.models import Upload, Snapshot, Scenario

# Create or get test upload
upload, created = Upload.objects.get_or_create(
    name='test_upload_1',
    defaults={'file': 'test.csv'}
)
print(f"{'Created' if created else 'Found'} upload: {upload.name}")

# Create or get test snapshot
snapshot, created = Snapshot.objects.get_or_create(
    name='test_snapshot_1',
    defaults={'linked_upload': upload}
)
print(f"{'Created' if created else 'Found'} snapshot: {snapshot.name}")

# Create or get test scenario
scenario, created = Scenario.objects.get_or_create(
    name='test_scenario_1',
    snapshot=snapshot,
    defaults={
        'param1': 1.5,
        'param2': 2,
        'param3': 50,
        'param4': True,
        'param5': False,
        'gpt_prompt': "Test prompt",
        'gpt_response': "Test response",
        'status': "created"
    }
)
print(f"{'Created' if created else 'Found'} scenario: {scenario.name}") 