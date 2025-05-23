import os
import json
import pandas as pd
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
sys.path.append(BACKEND_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()

from core.models import Snapshot, Upload, Scenario

test_data_dir = os.path.join(BASE_DIR, "test_data")
os.makedirs(test_data_dir, exist_ok=True)

test_vrp_data = """node,0,1,2,3,4,demand
0,0,10,20,30,40,0
1,10,0,15,25,35,10
2,20,15,0,10,20,20
3,30,25,10,0,15,30
4,40,35,20,15,0,10"""

test_vrp_file = os.path.join(test_data_dir, "test_infeasible_vrp.csv")
with open(test_vrp_file, 'w') as f:
    f.write(test_vrp_data)

print(f"Created test VRP data at {test_vrp_file}")

try:
    upload = Upload.objects.filter(name="test_infeasible_upload").first()
    if not upload:
        upload = Upload.objects.create(
            name="test_infeasible_upload",
            file=test_vrp_file,
            file_type="csv",
            rows=5,
            columns=7
        )
        print(f"Created test upload: {upload.name} (ID: {upload.id})")
    else:
        print(f"Using existing upload: {upload.name} (ID: {upload.id})")

    snapshot = Snapshot.objects.filter(name="test_infeasible_snapshot").first()
    if not snapshot:
        snapshot = Snapshot.objects.create(
            name="test_infeasible_snapshot",
            linked_upload=upload,
            description="Test snapshot for infeasible scenario"
        )
        print(f"Created test snapshot: {snapshot.name} (ID: {snapshot.id})")
    else:
        print(f"Using existing snapshot: {snapshot.name} (ID: {snapshot.id})")

    scenario = Scenario.objects.filter(name="test_infeasible_scenario").first()
    if not scenario:
        scenario = Scenario.objects.create(
            name="test_infeasible_scenario",
            snapshot=snapshot,
            param1=20,  # Capacity = 20
            param2=2,   # Vehicles = 2
            param3=50,  # Default value
            param4=False,
            param5=False,
            status="created",
            gpt_prompt="This scenario should be infeasible because total demand (70) > total capacity (40)"
        )
        print(f"Created test scenario: {scenario.name} (ID: {scenario.id})")
    else:
        print(f"Using existing scenario: {scenario.name} (ID: {scenario.id})")

    print("\nTest scenario created successfully!")
    print("To test the infeasibility explainer:")
    print("1. Run the Streamlit app: cd frontend && streamlit run main.py")
    print("2. Navigate to the Scenario Builder page")
    print("3. Find the scenario 'test_infeasible_scenario' and click 'Run Model'")
    print("4. After it fails, check the 'Show Details' section for the infeasibility explanation")

except Exception as e:
    print(f"Error creating test data: {e}")
