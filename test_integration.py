import os
import sys
import json
import subprocess
from pathlib import Path

def test_vrp_solver_integration():
    """Test the VRP solver integration with a simple scenario"""
    print("Testing VRP solver integration...")
    
    test_dir = os.path.join('test_data')
    os.makedirs(test_dir, exist_ok=True)
    
    snapshot_dir = os.path.join(test_dir, 'snapshots', 'test_snapshot')
    os.makedirs(snapshot_dir, exist_ok=True)
    
    snapshot_file = os.path.join(snapshot_dir, 'snapshot.csv')
    if not os.path.exists(snapshot_file):
        with open(snapshot_file, 'w') as f:
            f.write("node,demand,x,y\n")
            f.write("0,0,0,0\n")  # Depot
            f.write("1,10,5,5\n")  # Customer 1
            f.write("2,15,10,10\n")  # Customer 2
    
    scenario_dir = os.path.join(test_dir, 'scenarios', 'test_scenario')
    os.makedirs(scenario_dir, exist_ok=True)
    
    output_dir = os.path.join(scenario_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "name": "Test Scenario",
        "dataset_file_path": os.path.abspath(snapshot_file),
        "params": {
            "param1": 100.0,  # Vehicle capacity
            "param2": 1,      # Vehicle count
            "param3": 50,
            "param4": False,
            "param5": False
        },
        "gpt_prompt": "",
        "gpt_response": ""
    }
    
    scenario_json_path = os.path.join(scenario_dir, 'scenario.json')
    with open(scenario_json_path, 'w') as f:
        json.dump(scenario_config, f, indent=4)
    
    solver_script = os.path.abspath(os.path.join('backend', 'solver', 'vrp_solver.py'))
    
    result = subprocess.run(
        [sys.executable, solver_script, '--scenario-path', scenario_json_path],
        capture_output=True,
        text=True
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    
    if result.stderr:
        print(f"Stderr: {result.stderr}")
    
    model_lp_file = os.path.join(output_dir, "model.lp")
    alt_model_lp_file = os.path.join(scenario_dir, "model.lp")
    
    if os.path.exists(model_lp_file):
        print(f"✅ model.lp file created successfully at {model_lp_file}")
        print(f"File size: {os.path.getsize(model_lp_file)} bytes")
    elif os.path.exists(alt_model_lp_file):
        print(f"✅ model.lp file created successfully at {alt_model_lp_file}")
        print(f"File size: {os.path.getsize(alt_model_lp_file)} bytes")
        import shutil
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(alt_model_lp_file, model_lp_file)
        print(f"Copied model.lp to {model_lp_file}")
    else:
        print("❌ model.lp file not created")
    
    solution_file = os.path.join(output_dir, "solution_summary.json")
    alt_solution_file = os.path.join(scenario_dir, "solution_summary.json")
    current_dir_solution = "solution_summary.json"
    
    if os.path.exists(solution_file):
        print(f"✅ solution_summary.json created successfully at {solution_file}")
        with open(solution_file, 'r') as f:
            solution = json.load(f)
    elif os.path.exists(alt_solution_file):
        print(f"✅ solution_summary.json created successfully at {alt_solution_file}")
        with open(alt_solution_file, 'r') as f:
            solution = json.load(f)
        import shutil
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(alt_solution_file, solution_file)
        print(f"Copied solution_summary.json to {solution_file}")
    elif os.path.exists(current_dir_solution):
        print(f"✅ solution_summary.json created successfully in current directory")
        with open(current_dir_solution, 'r') as f:
            solution = json.load(f)
        import shutil
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(current_dir_solution, solution_file)
        print(f"Copied solution_summary.json to {solution_file}")
    else:
        print("❌ solution_summary.json not created")
        solution = None
    
    if solution:
        print(f"Solution: {json.dumps(solution, indent=2)}")
    
    return result.returncode == 0

if __name__ == "__main__":
    success = test_vrp_solver_integration()
    print(f"Test {'succeeded' if success else 'failed'}")
    sys.exit(0 if success else 1)
