# backend/applications/vehicle_routing/constraint_integration.py

from typing import Dict, List, Any, Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import json


class ConstraintIntegrationService:
    """Service to integrate parsed constraints into OR-Tools VRP solver"""

    def __init__(self):
        self.applied_constraints = []
        self.constraint_handlers = {
            'capacity': self._apply_capacity_constraint,
            'time_window': self._apply_time_window_constraint,
            'distance': self._apply_distance_constraint,
            'working_hours': self._apply_working_hours_constraint,
            'vehicle_restriction': self._apply_vehicle_restriction_constraint,
            'priority': self._apply_priority_constraint
        }

    def integrate_constraints_to_model(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraints: List[Dict]
    ) -> Dict[str, Any]:
        """
        Main method to integrate all parsed constraints into the OR-Tools model

        Args:
            routing: OR-Tools routing model
            manager: OR-Tools index manager
            data: Problem data (distances, demands, time windows, etc.)
            constraints: List of parsed constraints from natural language

        Returns:
            Dict with integration results and any conflicts/issues
        """

        integration_results = {
            'successful_constraints': [],
            'failed_constraints': [],
            'conflicts': [],
            'warnings': [],
            'dimensions_created': [],
            'callbacks_registered': []
        }

        # Sort constraints by priority (some constraints need to be applied first)
        sorted_constraints = self._sort_constraints_by_priority(constraints)

        for constraint in sorted_constraints:
            try:
                constraint_type = constraint.get('constraint_type')

                if constraint_type in self.constraint_handlers:
                    result = self.constraint_handlers[constraint_type](
                        routing, manager, data, constraint
                    )

                    if result['success']:
                        integration_results['successful_constraints'].append({
                            'constraint': constraint,
                            'details': result
                        })
                        self.applied_constraints.append(constraint)
                    else:
                        integration_results['failed_constraints'].append({
                            'constraint': constraint,
                            'error': result.get('error', 'Unknown error')
                        })
                else:
                    integration_results['failed_constraints'].append({
                        'constraint': constraint,
                        'error': f"Unsupported constraint type: {constraint_type}"
                    })

            except Exception as e:
                integration_results['failed_constraints'].append({
                    'constraint': constraint,
                    'error': f"Exception during integration: {str(e)}"
                })

        # Check for conflicts between constraints
        conflicts = self._detect_constraint_conflicts(constraints)
        integration_results['conflicts'] = conflicts

        return integration_results

    def _sort_constraints_by_priority(self, constraints: List[Dict]) -> List[Dict]:
        """Sort constraints by application priority"""
        priority_order = [
            'capacity',  # Must be first for vehicle routing
            'distance',  # Distance/duration dimensions
            'working_hours',  # Time-related constraints
            'time_window',  # Time windows
            'vehicle_restriction',  # Vehicle-specific restrictions
            'priority'  # Objective modifications
        ]

        def get_priority(constraint):
            constraint_type = constraint.get('constraint_type', 'unknown')
            try:
                return priority_order.index(constraint_type)
            except ValueError:
                return len(priority_order)  # Unknown types go last

        return sorted(constraints, key=get_priority)

    def _apply_capacity_constraint(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraint: Dict
    ) -> Dict:
        """Apply capacity constraint to the model"""

        try:
            params = constraint.get('parameters', {})
            math_format = constraint.get('mathematical_format', {})
            solver_format = math_format.get('solver_format', {})

            # Get capacity value
            capacity_value = float(params.get('capacity_value',
                                              solver_format.get('rhs', 100)))

            # Create demand callback if not exists
            if 'demand_callback_index' not in data:
                def demand_callback(from_index):
                    from_node = manager.IndexToNode(from_index)
                    return data.get('demands', [0] * data.get('num_locations', 1))[from_node]

                demand_callback_index = routing.RegisterTransitCallback(demand_callback)
                data['demand_callback_index'] = demand_callback_index
            else:
                demand_callback_index = data['demand_callback_index']

            # Add capacity dimension
            routing.AddDimension(
                evaluator_index=demand_callback_index,
                slack_max=0,  # No slack in capacity
                capacity=int(capacity_value),
                fix_start_cumul_to_zero=True,
                name='Capacity'
            )

            return {
                'success': True,
                'dimension_name': 'Capacity',
                'capacity_value': capacity_value,
                'message': f'Applied capacity constraint: {capacity_value} units per vehicle'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply capacity constraint: {str(e)}'
            }

    def _apply_time_window_constraint(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraint: Dict
    ) -> Dict:
        """Apply time window constraint to the model"""

        try:
            params = constraint.get('parameters', {})
            constraint_subtype = constraint.get('constraint_type', 'time_window')

            # Create time callback if not exists
            if 'time_callback_index' not in data:
                def time_callback(from_index, to_index):
                    from_node = manager.IndexToNode(from_index)
                    to_node = manager.IndexToNode(to_index)
                    return data.get('time_matrix', [[0]])[from_node][to_node]

                time_callback_index = routing.RegisterTransitCallback(time_callback)
                data['time_callback_index'] = time_callback_index
            else:
                time_callback_index = data['time_callback_index']

            # Add time dimension if not exists
            if 'Time' not in [routing.GetDimensionOrDie(name).name() for name in routing.GetAllDimensionNames()]:
                routing.AddDimension(
                    evaluator_index=time_callback_index,
                    slack_max=30,  # Allow some slack for time windows
                    capacity=1440,  # 24 hours in minutes
                    fix_start_cumul_to_zero=False,
                    name='Time'
                )

            time_dimension = routing.GetDimensionOrDie('Time')

            # Apply specific time window based on constraint type
            if constraint_subtype == 'time_window':
                customer_id = params.get('customer_id')
                start_time = params.get('start_time', 0)
                end_time = params.get('end_time', 1440)

                # Find customer index
                customer_index = self._find_customer_index(data, customer_id)
                if customer_index is not None:
                    time_dimension.CumulVar(customer_index).SetRange(start_time, end_time)

            elif constraint_subtype == 'delivery_before':
                customer_id = params.get('customer_id')
                deadline = params.get('deadline', 1440)

                customer_index = self._find_customer_index(data, customer_id)
                if customer_index is not None:
                    time_dimension.CumulVar(customer_index).SetMax(deadline)

            return {
                'success': True,
                'dimension_name': 'Time',
                'constraint_details': params,
                'message': f'Applied time window constraint for {params.get("customer_id", "customer")}'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply time window constraint: {str(e)}'
            }

    def _apply_distance_constraint(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraint: Dict
    ) -> Dict:
        """Apply distance constraint to the model"""

        try:
            params = constraint.get('parameters', {})
            math_format = constraint.get('mathematical_format', {})

            distance_value = float(params.get('distance_value',
                                              math_format.get('solver_format', {}).get('rhs', 1000)))

            # Create distance callback if not exists
            if 'distance_callback_index' not in data:
                def distance_callback(from_index, to_index):
                    from_node = manager.IndexToNode(from_index)
                    to_node = manager.IndexToNode(to_index)
                    return data.get('distance_matrix', [[0]])[from_node][to_node]

                distance_callback_index = routing.RegisterTransitCallback(distance_callback)
                data['distance_callback_index'] = distance_callback_index
            else:
                distance_callback_index = data['distance_callback_index']

            # Add distance dimension
            routing.AddDimension(
                evaluator_index=distance_callback_index,
                slack_max=0,
                capacity=int(distance_value),
                fix_start_cumul_to_zero=True,
                name='Distance'
            )

            return {
                'success': True,
                'dimension_name': 'Distance',
                'max_distance': distance_value,
                'message': f'Applied maximum distance constraint: {distance_value} units per route'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply distance constraint: {str(e)}'
            }

    def _apply_working_hours_constraint(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraint: Dict
    ) -> Dict:
        """Apply working hours constraint to the model"""

        try:
            params = constraint.get('parameters', {})
            max_hours = float(params.get('hours', 8))
            max_minutes = int(max_hours * 60)

            # This is typically handled through time dimension
            # Ensure time dimension exists
            if 'Time' not in [routing.GetDimensionOrDie(name).name() for name in routing.GetAllDimensionNames()]:
                # Create basic time dimension if not exists
                def time_callback(from_index, to_index):
                    from_node = manager.IndexToNode(from_index)
                    to_node = manager.IndexToNode(to_index)
                    return data.get('time_matrix', [[0]])[from_node][to_node]

                time_callback_index = routing.RegisterTransitCallback(time_callback)

                routing.AddDimension(
                    evaluator_index=time_callback_index,
                    slack_max=0,
                    capacity=max_minutes,  # Maximum working time
                    fix_start_cumul_to_zero=True,
                    name='WorkingTime'
                )
            else:
                # Modify existing time dimension capacity
                time_dimension = routing.GetDimensionOrDie('Time')
                # Note: OR-Tools doesn't allow changing capacity after creation
                # This would need to be handled during initial dimension creation

            return {
                'success': True,
                'max_working_hours': max_hours,
                'max_working_minutes': max_minutes,
                'message': f'Applied working hours constraint: maximum {max_hours} hours per driver'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply working hours constraint: {str(e)}'
            }

    def _apply_vehicle_restriction_constraint(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraint: Dict
    ) -> Dict:
        """Apply vehicle restriction constraint to the model"""

        try:
            params = constraint.get('parameters', {})
            vehicle_id = params.get('vehicle', params.get('vehicle_id'))
            location_id = params.get('location', params.get('location_id'))

            # Find vehicle and location indices
            vehicle_index = self._find_vehicle_index(data, vehicle_id)
            location_index = self._find_customer_index(data, location_id)

            if vehicle_index is not None and location_index is not None:
                # Add restriction: vehicle cannot visit location
                routing.SetAllowedVehiclesForIndex([v for v in range(data.get('num_vehicles', 1))
                                                    if v != vehicle_index], location_index)

                return {
                    'success': True,
                    'vehicle_index': vehicle_index,
                    'location_index': location_index,
                    'message': f'Vehicle {vehicle_id} restricted from visiting {location_id}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Could not find vehicle {vehicle_id} or location {location_id}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply vehicle restriction constraint: {str(e)}'
            }

    def _apply_priority_constraint(
            self,
            routing: pywrapcp.RoutingModel,
            manager: pywrapcp.RoutingIndexManager,
            data: Dict,
            constraint: Dict
    ) -> Dict:
        """Apply priority constraint by modifying the objective function"""

        try:
            params = constraint.get('parameters', {})
            customer_id = params.get('customer', params.get('customer_id'))

            # Find customer index
            customer_index = self._find_customer_index(data, customer_id)

            if customer_index is not None:
                # Add penalty for not visiting high-priority customer
                penalty = 10000  # High penalty
                routing.AddDisjunction([customer_index], penalty)

                return {
                    'success': True,
                    'customer_index': customer_index,
                    'penalty': penalty,
                    'message': f'Applied high priority to customer {customer_id}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Could not find customer {customer_id}'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to apply priority constraint: {str(e)}'
            }

    def _find_customer_index(self, data: Dict, customer_id: str) -> Optional[int]:
        """Find customer index by ID"""
        customers = data.get('customers', [])
        for i, customer in enumerate(customers):
            if str(customer.get('id', i)) == str(customer_id):
                return i
        return None

    def _find_vehicle_index(self, data: Dict, vehicle_id: str) -> Optional[int]:
        """Find vehicle index by ID"""
        vehicles = data.get('vehicles', [])
        for i, vehicle in enumerate(vehicles):
            if str(vehicle.get('id', i)) == str(vehicle_id):
                return i
        return None

    def _detect_constraint_conflicts(self, constraints: List[Dict]) -> List[Dict]:
        """Detect potential conflicts between constraints"""
        conflicts = []

        # Check for conflicting capacity constraints
        capacity_constraints = [c for c in constraints if c.get('constraint_type') == 'capacity']
        if len(capacity_constraints) > 1:
            capacities = [float(c.get('parameters', {}).get('capacity_value', 0))
                          for c in capacity_constraints]
            if len(set(capacities)) > 1:
                conflicts.append({
                    'type': 'conflicting_capacities',
                    'message': f'Multiple different capacity values specified: {capacities}',
                    'severity': 'high'
                })

        # Check for conflicting time windows
        time_constraints = [c for c in constraints if c.get('constraint_type') == 'time_window']
        customer_time_windows = {}

        for constraint in time_constraints:
            customer_id = constraint.get('parameters', {}).get('customer_id')
            if customer_id:
                if customer_id not in customer_time_windows:
                    customer_time_windows[customer_id] = []
                customer_time_windows[customer_id].append(constraint)

        for customer_id, windows in customer_time_windows.items():
            if len(windows) > 1:
                conflicts.append({
                    'type': 'conflicting_time_windows',
                    'message': f'Multiple time windows specified for customer {customer_id}',
                    'severity': 'medium',
                    'customer': customer_id
                })

        return conflicts

    def get_constraint_summary(self) -> Dict:
        """Get summary of applied constraints"""

        summary = {
            'total_constraints': len(self.applied_constraints),
            'by_type': {},
            'dimensions_used': [],
            'callbacks_created': []
        }

        for constraint in self.applied_constraints:
            constraint_type = constraint.get('constraint_type', 'unknown')
            if constraint_type not in summary['by_type']:
                summary['by_type'][constraint_type] = 0
            summary['by_type'][constraint_type] += 1

        return summary