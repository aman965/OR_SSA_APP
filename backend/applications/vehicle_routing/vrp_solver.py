# backend/applications/vehicle_routing/vrp_solver.py

import pulp
import numpy as np
from typing import Dict, List, Optional, Tuple
import time
import json
from .constraint_processor import ConstraintProcessor
from .models import VRPProblem, VRPSolution, save_solution


class VRPSolverPuLP:
    """
    Vehicle Routing Problem solver using PuLP with natural language constraint support
    Adapted from OR-Tools to work with your existing PuLP + CBC setup
    """

    def __init__(self, use_llm: bool = False, llm_api_key: Optional[str] = None):
        self.constraint_processor = ConstraintProcessor(use_llm, llm_api_key)
        self.problem_data = {}
        self.processed_constraints = []
        self.pulp_problem = None
        self.variables = {}
        self.solution_data = {}

    def setup_problem(self, problem_data: Dict):
        """
        Setup the VRP problem data

        Expected problem_data format:
        {
            'distance_matrix': [[0, 10, 15], [10, 0, 20], [15, 20, 0]],
            'customers': [{'id': '0', 'demand': 0}, {'id': '1', 'demand': 5}, ...],
            'vehicles': [{'id': '1', 'capacity': 100}, {'id': '2', 'capacity': 100}],
            'depot': 0,
            'num_vehicles': 2
        }
        """

        # Validate required fields
        required_fields = ['distance_matrix', 'num_vehicles', 'depot']
        for field in required_fields:
            if field not in problem_data:
                raise ValueError(f"Missing required field: {field}")

        self.problem_data = problem_data

        # Set default values
        if 'customers' not in problem_data:
            num_locations = len(problem_data['distance_matrix'])
            problem_data['customers'] = [
                {'id': str(i), 'demand': 1 if i > 0 else 0}
                for i in range(num_locations)
            ]

        if 'vehicles' not in problem_data:
            problem_data['vehicles'] = [
                {'id': str(i), 'capacity': 100}
                for i in range(problem_data['num_vehicles'])
            ]

        print(
            f"✅ Problem setup complete: {len(problem_data['customers'])} locations, {problem_data['num_vehicles']} vehicles")

    def add_constraint_from_prompt(self, prompt: str) -> Dict:
        """Add a constraint from natural language prompt"""
        result = self.constraint_processor.process_constraint(prompt, self.problem_data)

        if result['success']:
            self.processed_constraints.append(result['constraint'])
            print(f"✅ Constraint added: {prompt}")
        else:
            print(f"❌ Failed to add constraint: {result['errors']}")

        return result

    def add_multiple_constraints(self, constraint_prompts: List[str]) -> Dict:
        """Add multiple constraints from natural language prompts"""
        results = self.constraint_processor.process_multiple_constraints(
            constraint_prompts, self.problem_data
        )

        # Add successful constraints
        for item in results['successful']:
            self.processed_constraints.append(item['constraint'])

        print(f"✅ Added {len(results['successful'])}/{len(constraint_prompts)} constraints")
        if results['conflicts']:
            print(f"⚠️ Found {len(results['conflicts'])} potential conflicts")

        return results

    def solve(self, time_limit: int = 300, verbose: bool = True) -> Dict:
        """
        Solve the VRP with all processed constraints using PuLP

        Args:
            time_limit: Maximum solving time in seconds
            verbose: Print solving progress

        Returns:
            Dict with solution results
        """

        if not self.problem_data:
            return {'success': False, 'error': 'No problem data provided'}

        start_time = time.time()

        try:
            # Step 1: Create PuLP problem
            self._create_pulp_problem()

            # Step 2: Create decision variables
            self._create_variables()

            # Step 3: Set objective function
            self._set_objective()

            # Step 4: Add basic VRP constraints
            self._add_basic_constraints()

            # Step 5: Add natural language constraints
            self._add_processed_constraints()

            # Step 6: Solve
            if verbose:
                print(f"🚀 Solving VRP with {len(self.processed_constraints)} additional constraints...")

            # Use CBC solver with time limit
            solver = pulp.PULP_CBC_CMD(timeLimit=time_limit, msg=verbose)
            self.pulp_problem.solve(solver)

            solve_time = time.time() - start_time

            # Step 7: Process results
            if self.pulp_problem.status == pulp.LpStatusOptimal:
                if verbose:
                    print(f"✅ Optimal solution found in {solve_time:.2f} seconds!")

                solution = self._extract_solution()
                solution['solve_time'] = solve_time
                solution['status'] = 'optimal'
                solution['success'] = True

                return solution

            elif self.pulp_problem.status == pulp.LpStatusFeasible:
                if verbose:
                    print(f"✅ Feasible solution found in {solve_time:.2f} seconds")

                solution = self._extract_solution()
                solution['solve_time'] = solve_time
                solution['status'] = 'feasible'
                solution['success'] = True

                return solution

            else:
                status_names = {
                    pulp.LpStatusInfeasible: 'infeasible',
                    pulp.LpStatusUnbounded: 'unbounded',
                    pulp.LpStatusUndefined: 'undefined'
                }

                status = status_names.get(self.pulp_problem.status, 'unknown')

                return {
                    'success': False,
                    'status': status,
                    'solve_time': solve_time,
                    'error': f'Problem is {status}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Solving failed: {str(e)}',
                'solve_time': time.time() - start_time
            }

    def _create_pulp_problem(self):
        """Create the main PuLP optimization problem"""
        self.pulp_problem = pulp.LpProblem("VRP_with_Constraints", pulp.LpMinimize)

    def _create_variables(self):
        """Create decision variables for the VRP"""
        num_locations = len(self.problem_data['distance_matrix'])
        num_vehicles = self.problem_data['num_vehicles']

        # Binary variables: x[i][j][k] = 1 if vehicle k goes from location i to j
        self.variables['x'] = {}
        for i in range(num_locations):
            self.variables['x'][i] = {}
            for j in range(num_locations):
                if i != j:  # No self-loops
                    self.variables['x'][i][j] = {}
                    for k in range(num_vehicles):
                        var_name = f"x_{i}_{j}_{k}"
                        self.variables['x'][i][j][k] = pulp.LpVariable(
                            var_name, cat='Binary'
                        )

        # Continuous variables for arrival times (for time window constraints)
        self.variables['arrival_time'] = {}
        for i in range(num_locations):
            self.variables['arrival_time'][i] = {}
            for k in range(num_vehicles):
                var_name = f"arrival_{i}_{k}"
                self.variables['arrival_time'][i][k] = pulp.LpVariable(
                    var_name, lowBound=0, cat='Continuous'
                )

        # Vehicle usage variables
        self.variables['vehicle_used'] = {}
        for k in range(num_vehicles):
            var_name = f"vehicle_used_{k}"
            self.variables['vehicle_used'][k] = pulp.LpVariable(
                var_name, cat='Binary'
            )

    def _set_objective(self):
        """Set the objective function (minimize total distance)"""
        distance_matrix = self.problem_data['distance_matrix']
        num_locations = len(distance_matrix)
        num_vehicles = self.problem_data['num_vehicles']

        # Minimize total travel distance
        objective = 0
        for i in range(num_locations):
            for j in range(num_locations):
                if i != j:
                    for k in range(num_vehicles):
                        objective += (
                                distance_matrix[i][j] *
                                self.variables['x'][i][j][k]
                        )

        # Add vehicle fixed costs if specified
        vehicles = self.problem_data.get('vehicles', [])
        for k, vehicle in enumerate(vehicles):
            if k < num_vehicles:
                fixed_cost = vehicle.get('fixed_cost', 0)
                if fixed_cost > 0:
                    objective += fixed_cost * self.variables['vehicle_used'][k]

        self.pulp_problem += objective

    def _add_basic_constraints(self):
        """Add basic VRP constraints"""
        num_locations = len(self.problem_data['distance_matrix'])
        num_vehicles = self.problem_data['num_vehicles']
        depot = self.problem_data['depot']

        # 1. Each customer is visited exactly once (except depot)
        for j in range(num_locations):
            if j != depot:
                constraint = 0
                for i in range(num_locations):
                    if i != j:
                        for k in range(num_vehicles):
                            constraint += self.variables['x'][i][j][k]

                self.pulp_problem += constraint == 1, f"visit_customer_{j}"

        # 2. Flow conservation: if a vehicle enters a location, it must leave
        for i in range(num_locations):
            for k in range(num_vehicles):
                inflow = 0
                outflow = 0

                for j in range(num_locations):
                    if i != j:
                        inflow += self.variables['x'][j][i][k]
                        outflow += self.variables['x'][i][j][k]

                self.pulp_problem += inflow == outflow, f"flow_conservation_{i}_{k}"

        # 3. Each vehicle starts from depot at most once
        for k in range(num_vehicles):
            constraint = 0
            for j in range(num_locations):
                if j != depot:
                    constraint += self.variables['x'][depot][j][k]

            self.pulp_problem += constraint <= 1, f"vehicle_start_{k}"

            # Link vehicle usage with depot departure
            self.pulp_problem += (
                    self.variables['vehicle_used'][k] == constraint
            ), f"vehicle_usage_{k}"

        # 4. Each vehicle returns to depot at most once
        for k in range(num_vehicles):
            constraint = 0
            for i in range(num_locations):
                if i != depot:
                    constraint += self.variables['x'][i][depot][k]

            self.pulp_problem += constraint <= 1, f"vehicle_return_{k}"

    def _add_processed_constraints(self):
        """Add constraints from natural language processing"""

        # Export constraints in PuLP format
        pulp_constraints = self.constraint_processor.export_constraints_for_solver(
            self.processed_constraints, 'pulp'
        )

        # Add capacity constraints
        for constraint in pulp_constraints['capacity_constraints']:
            self._add_capacity_constraint(constraint)

        # Add time constraints
        for constraint in pulp_constraints['time_constraints']:
            self._add_time_constraint(constraint)

        # Add distance constraints
        for constraint in pulp_constraints['distance_constraints']:
            self._add_distance_constraint(constraint)

        # Add vehicle restrictions
        for constraint in pulp_constraints['vehicle_restrictions']:
            self._add_vehicle_restriction(constraint)

        # Add vehicle count constraints
        for constraint in pulp_constraints['vehicle_count_constraints']:
            self._add_vehicle_count_constraint(constraint)

    def _add_capacity_constraint(self, constraint: Dict):
        """Add vehicle capacity constraint"""
        max_capacity = constraint['max_capacity']
        customers = self.problem_data.get('customers', [])
        num_vehicles = self.problem_data['num_vehicles']
        depot = self.problem_data['depot']

        # For each vehicle, total demand served must not exceed capacity
        for k in range(num_vehicles):
            total_demand = 0

            for j, customer in enumerate(customers):
                if j != depot:  # Skip depot
                    demand = customer.get('demand', 0)

                    # If vehicle visits customer j, add its demand
                    visits_customer = 0
                    for i in range(len(customers)):
                        if i != j:
                            visits_customer += self.variables['x'][i][j][k]

                    total_demand += demand * visits_customer

            self.pulp_problem += (
                    total_demand <= max_capacity
            ), f"capacity_vehicle_{k}"

        print(f"✅ Added capacity constraint: max {max_capacity} units per vehicle")

    def _add_time_constraint(self, constraint: Dict):
        """Add time window constraint"""
        constraint_type = constraint['type']
        customer_id = constraint.get('customer')
        time_bounds = constraint.get('time_bounds', {})

        # Find customer index
        customer_index = self._find_customer_index(customer_id)
        if customer_index is None:
            print(f"⚠️ Customer {customer_id} not found for time constraint")
            return

        num_vehicles = self.problem_data['num_vehicles']

        if constraint_type == 'time_window':
            # Customer must be visited within time window
            lower_bound = time_bounds.get('lower_bound', 0)
            upper_bound = time_bounds.get('upper_bound', 1440)  # 24 hours

            for k in range(num_vehicles):
                arrival_var = self.variables['arrival_time'][customer_index][k]

                # Only apply constraint if vehicle visits this customer
                visits = 0
                for i in range(len(self.problem_data['customers'])):
                    if i != customer_index:
                        visits += self.variables['x'][i][customer_index][k]

                # Big M constraint: if vehicle visits customer, respect time window
                M = 10000  # Large number

                self.pulp_problem += (
                        arrival_var >= lower_bound - M * (1 - visits)
                ), f"time_window_start_{customer_index}_{k}"

                self.pulp_problem += (
                        arrival_var <= upper_bound + M * (1 - visits)
                ), f"time_window_end_{customer_index}_{k}"

        elif constraint_type == 'delivery_before':
            # Customer must be visited before deadline
            deadline = time_bounds.get('rhs', 1440)

            for k in range(num_vehicles):
                arrival_var = self.variables['arrival_time'][customer_index][k]

                visits = 0
                for i in range(len(self.problem_data['customers'])):
                    if i != customer_index:
                        visits += self.variables['x'][i][customer_index][k]

                M = 10000
                self.pulp_problem += (
                        arrival_var <= deadline + M * (1 - visits)
                ), f"deadline_{customer_index}_{k}"

        print(f"✅ Added time constraint for customer {customer_id}")

    def _add_distance_constraint(self, constraint: Dict):
        """Add maximum distance constraint"""
        max_distance = constraint['max_distance']
        distance_matrix = self.problem_data['distance_matrix']
        num_locations = len(distance_matrix)
        num_vehicles = self.problem_data['num_vehicles']

        # For each vehicle, total distance must not exceed maximum
        for k in range(num_vehicles):
            total_distance = 0

            for i in range(num_locations):
                for j in range(num_locations):
                    if i != j:
                        total_distance += (
                                distance_matrix[i][j] *
                                self.variables['x'][i][j][k]
                        )

            self.pulp_problem += (
                    total_distance <= max_distance
            ), f"max_distance_vehicle_{k}"

        print(f"✅ Added distance constraint: max {max_distance} units per route")

    def _add_vehicle_restriction(self, constraint: Dict):
        """Add vehicle restriction constraint"""
        restriction_type = constraint['type']
        vehicle_id = constraint.get('vehicle')
        location_id = constraint.get('location')

        # Find indices
        vehicle_index = self._find_vehicle_index(vehicle_id)
        location_index = self._find_customer_index(location_id)

        if vehicle_index is None or location_index is None:
            print(f"⚠️ Could not find vehicle {vehicle_id} or location {location_id}")
            return

        num_locations = len(self.problem_data['customers'])

        if restriction_type == 'vehicle_location_forbidden':
            # Vehicle cannot visit location
            for i in range(num_locations):
                if i != location_index:
                    constraint_expr = self.variables['x'][i][location_index][vehicle_index]
                    self.pulp_problem += constraint_expr == 0, f"forbidden_{vehicle_index}_{location_index}_{i}"

        elif restriction_type == 'vehicle_location_exclusive':
            # Only this vehicle can visit location
            for k in range(self.problem_data['num_vehicles']):
                if k != vehicle_index:
                    for i in range(num_locations):
                        if i != location_index:
                            constraint_expr = self.variables['x'][i][location_index][k]
                            self.pulp_problem += constraint_expr == 0, f"exclusive_{k}_{location_index}_{i}"

        print(f"✅ Added vehicle restriction: {restriction_type}")

    def _add_vehicle_count_constraint(self, constraint: Dict):
        """Add vehicle count constraint"""
        constraint_type = constraint['type']
        count = constraint['count']
        operator = constraint['operator']
        
        num_vehicles = self.problem_data['num_vehicles']
        
        # Sum of all vehicle usage variables
        total_vehicles_used = 0
        for k in range(num_vehicles):
            total_vehicles_used += self.variables['vehicle_used'][k]
        
        if constraint_type == 'min_vehicles':
            self.pulp_problem += (
                total_vehicles_used >= count
            ), f"min_vehicles_{count}"
            print(f"✅ Added minimum vehicles constraint: at least {count} vehicles")
            
        elif constraint_type == 'max_vehicles':
            self.pulp_problem += (
                total_vehicles_used <= count
            ), f"max_vehicles_{count}"
            print(f"✅ Added maximum vehicles constraint: at most {count} vehicles")

    def _find_customer_index(self, customer_id: str) -> Optional[int]:
        """Find customer index by ID"""
        customers = self.problem_data.get('customers', [])
        for i, customer in enumerate(customers):
            if str(customer.get('id', i)) == str(customer_id):
                return i
        return None

    def _find_vehicle_index(self, vehicle_id: str) -> Optional[int]:
        """Find vehicle index by ID"""
        vehicles = self.problem_data.get('vehicles', [])
        for i, vehicle in enumerate(vehicles):
            if str(vehicle.get('id', i)) == str(vehicle_id):
                return i
        return None

    def _extract_solution(self) -> Dict:
        """Extract solution from solved PuLP problem"""
        num_locations = len(self.problem_data['distance_matrix'])
        num_vehicles = self.problem_data['num_vehicles']
        distance_matrix = self.problem_data['distance_matrix']

        routes = []
        total_distance = 0
        vehicles_used = 0

        # Extract routes for each vehicle
        for k in range(num_vehicles):
            route = {
                'vehicle_id': k, 
                'route': [], 
                'distance': 0, 
                'customers': [],
                'total_demand': 0,
                'load_utilization': 0.0,
                'customer_count': 0,
                'service_time': 0
            }

            # Check if vehicle is used
            if pulp.value(self.variables['vehicle_used'][k]) > 0.5:
                vehicles_used += 1

                # Find the route by following the x variables
                current_location = self.problem_data['depot']
                route['route'].append(current_location)

                visited = set([current_location])

                while True:
                    next_location = None

                    # Find next location in route
                    for j in range(num_locations):
                        if j not in visited:
                            if (current_location in self.variables['x'] and
                                    j in self.variables['x'][current_location] and
                                    k in self.variables['x'][current_location][j]):

                                x_val = pulp.value(self.variables['x'][current_location][j][k])
                                if x_val and x_val > 0.5:
                                    next_location = j
                                    break

                    if next_location is None:
                        # Return to depot
                        if current_location != self.problem_data['depot']:
                            route['route'].append(self.problem_data['depot'])
                            route['distance'] += distance_matrix[current_location][self.problem_data['depot']]
                        break
                    else:
                        route['route'].append(next_location)
                        route['distance'] += distance_matrix[current_location][next_location]
                        visited.add(next_location)
                        current_location = next_location

                        # Add customer info and calculate KPIs
                        if next_location != self.problem_data['depot']:
                            customers = self.problem_data.get('customers', [])
                            if next_location < len(customers):
                                customer = customers[next_location]
                                route['customers'].append(customer)
                                
                                # Update KPIs
                                route['total_demand'] += customer.get('demand', 0)
                                route['customer_count'] += 1
                                route['service_time'] += customer.get('service_time', 0)

            if len(route['route']) > 1:  # Vehicle has a route
                # Calculate final KPIs
                vehicles = self.problem_data.get('vehicles', [])
                if k < len(vehicles):
                    vehicle_capacity = vehicles[k].get('capacity', 100)
                    route['vehicle_capacity'] = vehicle_capacity
                    route['load_utilization'] = (route['total_demand'] / vehicle_capacity * 100) if vehicle_capacity > 0 else 0
                    route['capacity_remaining'] = vehicle_capacity - route['total_demand']
                
                # Add efficiency metrics
                route['distance_per_customer'] = route['distance'] / route['customer_count'] if route['customer_count'] > 0 else 0
                route['demand_per_distance'] = route['total_demand'] / route['distance'] if route['distance'] > 0 else 0
                
                routes.append(route)
                total_distance += route['distance']

        # Calculate objective value
        objective_value = pulp.value(self.pulp_problem.objective)

        return {
            'routes': routes,
            'total_distance': total_distance,
            'objective_value': objective_value,
            'vehicles_used': vehicles_used,
            'total_vehicles': num_vehicles,
            'solver': 'pulp_cbc',
            'constraint_count': len(self.processed_constraints),
            'is_optimal': self.pulp_problem.status == pulp.LpStatusOptimal
        }

    def get_constraint_summary(self) -> Dict:
        """Get summary of processed constraints"""
        return self.constraint_processor._generate_summary({
            'successful': [{'constraint': c} for c in self.processed_constraints],
            'failed': [],
            'conflicts': []
        })

    def save_to_database(self, session, problem_id: int, solution_data: Dict):
        """Save solution to database"""
        return save_solution(session, problem_id, solution_data)


# Example usage function
def solve_vrp_example():
    """Example of how to use the VRP solver with natural language constraints"""

    # Sample problem data
    problem_data = {
        'distance_matrix': [
            [0, 10, 15, 20, 12],
            [10, 0, 35, 25, 18],
            [15, 35, 0, 30, 22],
            [20, 25, 30, 0, 28],
            [12, 18, 22, 28, 0]
        ],
        'num_vehicles': 2,
        'depot': 0,
        'customers': [
            {'id': '0', 'name': 'Depot', 'demand': 0},
            {'id': '1', 'name': 'Customer A', 'demand': 5},
            {'id': '2', 'name': 'Customer B', 'demand': 8},
            {'id': '3', 'name': 'Customer C', 'demand': 6},
            {'id': '4', 'name': 'Customer D', 'demand': 4}
        ],
        'vehicles': [
            {'id': '1', 'name': 'Truck 1', 'capacity': 15},
            {'id': '2', 'name': 'Truck 2', 'capacity': 15}
        ]
    }

    # Create solver
    solver = VRPSolverPuLP(use_llm=False)  # Set to True if you have OpenAI API key
    solver.setup_problem(problem_data)

    # Add natural language constraints
    constraints = [
        "Each vehicle can carry maximum 15 units",
        "Vehicle 1 cannot visit Customer B",
        "Total route distance should not exceed 50 km"
    ]

    print("Adding constraints:")
    for constraint in constraints:
        result = solver.add_constraint_from_prompt(constraint)
        if result['success']:
            print(f"✅ {constraint}")
        else:
            print(f"❌ {constraint} - {result['errors']}")

    # Solve
    print("\nSolving VRP...")
    solution = solver.solve(time_limit=60, verbose=True)

    if solution['success']:
        print("\n🎉 Solution:")
        print(f"Total Distance: {solution['total_distance']}")
        print(f"Vehicles Used: {solution['vehicles_used']}/{solution['total_vehicles']}")
        print(f"Constraint Count: {solution['constraint_count']}")

        print("\nRoutes:")
        for route in solution['routes']:
            customer_names = [c.get('name', f"Customer {c['id']}") for c in route['customers']]
            print(f"Vehicle {route['vehicle_id']}: {' → '.join(customer_names)} (Distance: {route['distance']})")
    else:
        print(f"\n❌ Failed: {solution['error']}")


if __name__ == "__main__":
    solve_vrp_example()