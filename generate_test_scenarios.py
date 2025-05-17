import os
import sys
import django
import shutil
import json
import subprocess
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "backend"))
MEDIA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "media"))
sys.path.append(BACKEND_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'orsaas_backend.settings')
django.setup()

from core.models import Upload, Snapshot, Scenario
from django.core.files.base import ContentFile
from django.utils import timezone

def create_test_data():
    print("Creating test data...")
    
    upload_name = f"test_upload_{int(datetime.now().timestamp())}"
    upload_file_path = os.path.join(BASE_DIR, "test_data/vrp_test_data/test_vrp_data.csv")
    
    with open(upload_file_path, 'rb') as f:
        file_content = f.read()
    
    upload = Upload.objects.create(
        name=upload_name,
        uploaded_at=timezone.now()
    )
    upload.file.save(f"{upload_name}.csv", ContentFile(file_content))
    print(f"Created upload: {upload.name} (ID: {upload.id})")
    
    snapshot_name = f"test_snapshot_{int(datetime.now().timestamp())}"
    snapshot = Snapshot.objects.create(
        name=snapshot_name,
        created_at=timezone.now(),
        linked_upload=upload,
        description="Test snapshot for VRP data"
    )
    
    snapshot_dir = os.path.join(MEDIA_ROOT, "snapshots", str(snapshot.id))
    os.makedirs(snapshot_dir, exist_ok=True)
    
    snapshot_file_path = os.path.join(snapshot_dir, "snapshot.csv")
    shutil.copy2(upload.file.path, snapshot_file_path)
    print(f"Created snapshot: {snapshot.name} (ID: {snapshot.id})")
    
    scenario_params = [
        {"name": "High Capacity", "param1": 100.0, "param2": 2, "param3": 50, "param4": False, "param5": True},
        {"name": "Low Capacity", "param1": 25.0, "param2": 3, "param3": 75, "param4": True, "param5": False}
    ]
    
    scenarios = []
    for params in scenario_params:
        scenario = Scenario.objects.create(
            name=params["name"],
            snapshot=snapshot,
            param1=params["param1"],
            param2=params["param2"],
            param3=params["param3"],
            param4=params["param4"],
            param5=params["param5"],
            status="created"
        )
        
        scenario_dir = os.path.join(MEDIA_ROOT, "scenarios", str(scenario.id))
        output_dir = os.path.join(scenario_dir, "outputs")
        os.makedirs(scenario_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        scenario_data = {
            "scenario_id": str(scenario.id),
            "scenario_name": scenario.name,
            "snapshot_id": str(snapshot.id),
            "snapshot_name": snapshot.name,
            "dataset_file_path": os.path.join(MEDIA_ROOT, upload.file.name),
            "params": {
                "param1": scenario.param1,
                "param2": scenario.param2,
                "param3": scenario.param3,
                "param4": scenario.param4,
                "param5": scenario.param5,
            }
        }
        
        scenario_json_path = os.path.join(scenario_dir, "scenario.json")
        with open(scenario_json_path, 'w') as f:
            json.dump(scenario_data, f, indent=4)
        
        print(f"Created scenario: {scenario.name} (ID: {scenario.id})")
        scenarios.append(scenario)
        
        solver_path = os.path.join(BACKEND_PATH, "solver", "vrp_solver.py")
        try:
            result = subprocess.run(
                [sys.executable, solver_path, "--scenario-path", scenario_json_path],
                check=True,
                capture_output=True,
                text=True,
                timeout=180
            )
            print(f"Solver output for {scenario.name}: {result.stdout}")
            
            solution_path = os.path.join(output_dir, "solution_summary.json")
            if os.path.exists(solution_path):
                scenario.status = "solved"
                scenario.save()
                print(f"Scenario {scenario.name} solved successfully.")
            else:
                failure_path = os.path.join(output_dir, "failure_summary.json")
                if os.path.exists(failure_path):
                    scenario.status = "failed"
                    scenario.save()
                    print(f"Scenario {scenario.name} failed.")
        except Exception as e:
            print(f"Error running solver for {scenario.name}: {str(e)}")
            scenario.status = "failed"
            scenario.reason = str(e)
            scenario.save()
    
    print("Test data creation completed.")
    print(f"Created snapshot: {snapshot.name} (ID: {snapshot.id})")
    print(f"Created scenarios: {', '.join([s.name for s in scenarios])}")
    print("You can now test the comparison functionality by going to the compare page and selecting these scenarios.")

if __name__ == "__main__":
    create_test_data()
