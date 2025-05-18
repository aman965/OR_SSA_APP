import os
import django
import sys
import json

# Set up Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()

from core.models import Scenario

def reset_scenario(scenario):
    """Reset a single scenario and its associated files"""
    print(f"\nProcessing scenario: {scenario.name} (ID: {scenario.id})")
    print(f"Current status: {scenario.status}")
    
    # Reset scenario status
    scenario.status = 'created'
    scenario.reason = ''
    scenario.save()
    print(f"Updated status to: {scenario.status}")
    
    # Check and clean up any output files
    scenario_dir = os.path.join(BASE_DIR, "media", "scenarios", str(scenario.id))
    if os.path.exists(scenario_dir):
        print(f"Found scenario directory: {scenario_dir}")
        # Remove any existing output files
        for file in ['solution_summary.json', 'failure_summary.json', 'compare_metrics.json']:
            file_path = os.path.join(scenario_dir, file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed file: {file}")
                except Exception as e:
                    print(f"Error removing {file}: {str(e)}")
    else:
        print(f"Warning: Scenario directory not found: {scenario_dir}")

# Get all scenarios
all_scenarios = Scenario.objects.all()
print(f"\nTotal scenarios in database: {all_scenarios.count()}")

# Reset all scenarios
print("\nResetting all scenarios to 'created' state...")
for scenario in all_scenarios:
    reset_scenario(scenario)

# Print final status of all scenarios
print("\nFinal status of all scenarios:")
for scenario in Scenario.objects.all():
    print(f"- {scenario.name}: {scenario.status}")

print("\nDone!")
