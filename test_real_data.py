import os
import sys
import json
import subprocess
import shutil
from pathlib import Path

def test_vrp_solver_with_real_data():
    """Test the VRP solver integration with real data"""
    print("Testing VRP solver with real data...")
    
    test_dir = os.path.join('test_data', 'real_test')
    os.makedirs(test_dir, exist_ok=True)
    
    real_data_csv = os.path.join(test_dir, 'Test_VRP.csv')
    if not os.path.exists(real_data_csv):
        print(f"Error: Test data file not found at {real_data_csv}")
        return False
    
    scenario_dir = os.path.join(test_dir, 'scenarios', 'real_scenario')
    os.makedirs(scenario_dir, exist_ok=True)
    
    output_dir = os.path.join(scenario_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    scenario_config = {
        "name": "Real Data Test Scenario",
        "dataset_file_path": os.path.abspath(real_data_csv),
        "params": {
            "param1": 100.0,  # Vehicle capacity
            "param2": 2,      # Vehicle count
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
        shutil.copy2(alt_solution_file, solution_file)
        print(f"Copied solution_summary.json to {solution_file}")
    elif os.path.exists(current_dir_solution):
        print(f"✅ solution_summary.json created successfully in current directory")
        with open(current_dir_solution, 'r') as f:
            solution = json.load(f)
        shutil.copy2(current_dir_solution, solution_file)
        print(f"Copied solution_summary.json to {solution_file}")
    else:
        print("❌ solution_summary.json not created")
        solution = None
    
    if solution:
        print(f"Solution: {json.dumps(solution, indent=2)}")
    
    if not solution:
        failure_file = os.path.join(output_dir, "failure_summary.json")
        alt_failure_file = os.path.join(scenario_dir, "failure_summary.json")
        
        if os.path.exists(failure_file):
            print(f"⚠️ failure_summary.json found at {failure_file}")
            with open(failure_file, 'r') as f:
                failure = json.load(f)
            print(f"Failure: {json.dumps(failure, indent=2)}")
        elif os.path.exists(alt_failure_file):
            print(f"⚠️ failure_summary.json found at {alt_failure_file}")
            with open(alt_failure_file, 'r') as f:
                failure = json.load(f)
            print(f"Failure: {json.dumps(failure, indent=2)}")
        else:
            print("❌ No solution or failure files found")
    
    return result.returncode == 0

if __name__ == "__main__":
    success = test_vrp_solver_with_real_data()
    print(f"Test {'succeeded' if success else 'failed'}")
    sys.exit(0 if success else 1)
