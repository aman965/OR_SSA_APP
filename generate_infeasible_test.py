import os
import json
import pandas as pd
import numpy as np

scenario_dir = 'test_data/scenarios/infeasible_test'
os.makedirs(scenario_dir, exist_ok=True)
os.makedirs('test_data', exist_ok=True)

scenario = {
    'params': {
        'param1': 10,  # Very small capacity
        'param2': 1,   # Only one vehicle
        'vehicle_limit': 1
    },
    'dataset_file_path': os.path.abspath('test_data/test_vrp_data.csv')
}

n = 5
dist_matrix = np.zeros((n, n))
for i in range(n):
    for j in range(n):
        if i != j:
            dist_matrix[i, j] = np.sqrt((i-j)**2) * 10

demands = [0, 5, 4, 6, 7]  # Total demand = 22, capacity = 10

df = pd.DataFrame(dist_matrix)
df['demand'] = demands

df.to_csv('test_data/test_vrp_data.csv', index=False)

with open(os.path.join(scenario_dir, 'scenario.json'), 'w') as f:
    json.dump(scenario, f, indent=2)

print(f'Created test scenario in {scenario_dir}')
print(f'Created test data in test_data/test_vrp_data.csv')

from backend.solver.vrp_solver import main
import sys

sys.argv = ['vrp_solver.py', '--scenario-path', os.path.join(scenario_dir, 'scenario.json')]

try:
    main()
    print("Solver completed successfully")
except Exception as e:
    print(f"Solver failed as expected (infeasible model): {e}")
    print("Check for model.lp file in the scenario directory")

model_lp_path = os.path.join(scenario_dir, 'model.lp')
if os.path.exists(model_lp_path):
    print(f"model.lp file created at {model_lp_path}")
    with open(model_lp_path, 'r') as f:
        print("\nFirst 20 lines of model.lp:")
        for i, line in enumerate(f):
            if i < 20:
                print(line.strip())
            else:
                break
else:
    print(f"model.lp file not found at {model_lp_path}")
