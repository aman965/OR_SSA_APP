# backend/applications/vehicle_routing/constraint_patterns.py

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ConstraintPattern:
    pattern: str
    constraint_type: str
    parameter_groups: List[str]
    conversion_function: str


class VRPConstraintMatcher:
    def __init__(self):
        self.patterns = self._define_patterns()

    def _define_patterns(self) -> Dict[str, List[ConstraintPattern]]:
        return {
            'capacity': [
                ConstraintPattern(
                    pattern=r"vehicle(?:s)?\s+capacity\s+(?:should\s+)?(?:not\s+)?(?:exceed|be\s+(?:less\s+than|under|below|at\s+most))\s+(\d+(?:\.\d+)?)\s*(\w+)?",
                    constraint_type="vehicle_capacity_max",
                    parameter_groups=["capacity_value", "unit"],
                    conversion_function="convert_capacity_constraint"
                ),
                ConstraintPattern(
                    pattern=r"(?:each\s+)?vehicle\s+can\s+carry\s+(?:at\s+most\s+|maximum\s+)?(\d+(?:\.\d+)?)\s*(\w+)?",
                    constraint_type="vehicle_capacity_max",
                    parameter_groups=["capacity_value", "unit"],
                    conversion_function="convert_capacity_constraint"
                ),
                ConstraintPattern(
                    pattern=r"(?:each\s+)?vehicle\s+can\s+carry\s+(?:a\s+)?maximum\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*(\w+)?",
                    constraint_type="vehicle_capacity_max",
                    parameter_groups=["capacity_value", "unit"],
                    conversion_function="convert_capacity_constraint"
                ),
                ConstraintPattern(
                    pattern=r"maximum\s+load\s+(?:per\s+vehicle\s+)?(?:is\s+)?(\d+(?:\.\d+)?)\s*(\w+)?",
                    constraint_type="vehicle_capacity_max",
                    parameter_groups=["capacity_value", "unit"],
                    conversion_function="convert_capacity_constraint"
                ),
                ConstraintPattern(
                    pattern=r"at\s+max(?:imum)?\s+(\d+(?:\.\d+)?)\s*(\w+)?\s+capacity\s+should\s+be\s+used",
                    constraint_type="vehicle_capacity_max",
                    parameter_groups=["capacity_value", "unit"],
                    conversion_function="convert_capacity_constraint"
                )
            ],

            'time_window': [
                ConstraintPattern(
                    pattern=r"(?:deliver\s+to\s+|visit\s+)?(?:customer\s+)?([A-Za-z0-9]+)\s+(?:before|by)\s+(\d{1,2}):?(\d{2})?\s*(AM|PM)?",
                    constraint_type="delivery_before",
                    parameter_groups=["customer_id", "hour", "minute", "period"],
                    conversion_function="convert_time_window_constraint"
                ),
                ConstraintPattern(
                    pattern=r"(?:customer\s+)?([A-Za-z0-9]+).*between.*?(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?.*?and.*?(\d{1,2}):?(\d{2})?\s*(am|pm|AM|PM)?",
                    constraint_type="time_window",
                    parameter_groups=["customer_id", "start_hour", "start_minute", "start_period", "end_hour",
                                      "end_minute", "end_period"],
                    conversion_function="convert_time_window_constraint"
                ),
                ConstraintPattern(
                    pattern=r"(?:customer\s+)?([A-Za-z0-9]+)\s+(?:must\s+be\s+visited\s+between\s+)(\d{1,2}):(\d{2})\s*(AM|PM)?\s+(?:and\s+)(\d{1,2}):(\d{2})\s*(AM|PM)?",
                    constraint_type="time_window",
                    parameter_groups=["customer_id", "start_hour", "start_minute", "start_period", "end_hour",
                                      "end_minute", "end_period"],
                    conversion_function="convert_time_window_constraint"
                )
            ],

            'distance': [
                ConstraintPattern(
                    pattern=r"(?:total\s+)?(?:route\s+)?distance\s+(?:should\s+)?(?:not\s+)?(?:exceed|be\s+(?:less\s+than|under|below|at\s+most))\s+(\d+(?:\.\d+)?)\s*(km|miles?|kilometers?)?",
                    constraint_type="max_route_distance",
                    parameter_groups=["distance_value", "unit"],
                    conversion_function="convert_distance_constraint"
                ),
                ConstraintPattern(
                    pattern=r"distance\s+between\s+(?:any\s+)?(?:two\s+)?(?:consecutive\s+)?stops?\s+(?:should\s+be\s+)?(?:less\s+than|under|below|at\s+most)\s+(\d+(?:\.\d+)?)\s*(km|miles?|kilometers?)?",
                    constraint_type="max_consecutive_distance",
                    parameter_groups=["distance_value", "unit"],
                    conversion_function="convert_distance_constraint"
                )
            ],

            'working_hours': [
                ConstraintPattern(
                    pattern=r"(?:driver|vehicle)\s+(?:should\s+)?(?:not\s+)?work\s+(?:more\s+than\s+)?(\d+(?:\.\d+)?)\s+hours?",
                    constraint_type="max_working_hours",
                    parameter_groups=["hours"],
                    conversion_function="convert_working_hours_constraint"
                ),
                ConstraintPattern(
                    pattern=r"(?:maximum\s+)?(?:shift\s+)?(?:duration\s+)?(?:is\s+)?(\d+(?:\.\d+)?)\s+hours?",
                    constraint_type="max_working_hours",
                    parameter_groups=["hours"],
                    conversion_function="convert_working_hours_constraint"
                )
            ],

            'vehicle_restriction': [
                ConstraintPattern(
                    pattern=r"vehicle\s+([A-Za-z0-9]+)\s+(?:cannot|should\s+not|must\s+not)\s+visit\s+(?:location\s+|customer\s+)?([A-Za-z0-9]+)",
                    constraint_type="vehicle_location_forbidden",
                    parameter_groups=["vehicle_id", "location_id"],
                    conversion_function="convert_vehicle_restriction_constraint"
                ),
                ConstraintPattern(
                    pattern=r"(?:only\s+)?vehicle\s+([A-Za-z0-9]+)\s+(?:can|should|must)\s+visit\s+(?:location\s+|customer\s+)?([A-Za-z0-9]+)",
                    constraint_type="vehicle_location_exclusive",
                    parameter_groups=["vehicle_id", "location_id"],
                    conversion_function="convert_vehicle_restriction_constraint"
                )
            ],

            'priority': [
                ConstraintPattern(
                    pattern=r"(?:customer\s+|location\s+)?([A-Za-z0-9]+)\s+(?:has\s+)?(?:high|highest)\s+priority",
                    constraint_type="high_priority",
                    parameter_groups=["customer_id"],
                    conversion_function="convert_priority_constraint"
                ),
                ConstraintPattern(
                    pattern=r"visit\s+(?:customer\s+|location\s+)?([A-Za-z0-9]+)\s+first",
                    constraint_type="visit_first",
                    parameter_groups=["customer_id"],
                    conversion_function="convert_priority_constraint"
                )
            ],

            'vehicle_count': [
                ConstraintPattern(
                    pattern=r"m(?:in|im)(?:imum)?\s+(\d+)\s+vehicles?\s+should\s+be\s+used",
                    constraint_type="min_vehicles",
                    parameter_groups=["min_vehicles"],
                    conversion_function="convert_vehicle_count_constraint"
                ),
                ConstraintPattern(
                    pattern=r"use\s+at\s+least\s+(\d+)\s+vehicles?",
                    constraint_type="min_vehicles",
                    parameter_groups=["min_vehicles"],
                    conversion_function="convert_vehicle_count_constraint"
                ),
                ConstraintPattern(
                    pattern=r"need\s+(?:at\s+least\s+)?(\d+)\s+vehicles?",
                    constraint_type="min_vehicles",
                    parameter_groups=["min_vehicles"],
                    conversion_function="convert_vehicle_count_constraint"
                ),
                ConstraintPattern(
                    pattern=r"require\s+(?:at\s+least\s+)?(\d+)\s+vehicles?",
                    constraint_type="min_vehicles",
                    parameter_groups=["min_vehicles"],
                    conversion_function="convert_vehicle_count_constraint"
                ),
                ConstraintPattern(
                    pattern=r"max(?:imum)?\s+(\d+)\s+vehicles?\s+should\s+be\s+used",
                    constraint_type="max_vehicles",
                    parameter_groups=["max_vehicles"],
                    conversion_function="convert_vehicle_count_constraint"
                ),
                ConstraintPattern(
                    pattern=r"use\s+(?:at\s+most\s+|no\s+more\s+than\s+)?(\d+)\s+vehicles?",
                    constraint_type="max_vehicles",
                    parameter_groups=["max_vehicles"],
                    conversion_function="convert_vehicle_count_constraint"
                )
            ]
        }

    def match_constraint(self, prompt: str) -> Optional[Tuple[str, Dict]]:
        """Match prompt against predefined patterns"""
        prompt_lower = prompt.lower().strip()

        for category, patterns in self.patterns.items():
            for pattern_obj in patterns:
                match = re.search(pattern_obj.pattern, prompt_lower)
                if match:
                    # Extract parameters based on groups
                    params = {}
                    for i, param_name in enumerate(pattern_obj.parameter_groups):
                        if i + 1 <= len(match.groups()) and match.group(i + 1):
                            params[param_name] = match.group(i + 1)

                    return pattern_obj.constraint_type, {
                        'parameters': params,
                        'conversion_function': pattern_obj.conversion_function,
                        'original_prompt': prompt,
                        'matched_pattern': pattern_obj.pattern
                    }

        return None


class ConstraintConverter:
    """Convert extracted parameters to mathematical constraints"""

    def convert_capacity_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert capacity constraint to mathematical format"""
        capacity_value = float(params['capacity_value'])
        unit = params.get('unit', 'units')

        return {
            'type': 'capacity',
            'mathematical_form': f"sum(x_ij * demand_j for all j in route) <= {capacity_value}",
            'solver_format': {
                'constraint_type': 'linear',
                'coefficients': 'demand_vector',
                'operator': '<=',
                'rhs': capacity_value,
                'variables': 'route_variables'
            },
            'unit': unit,
            'description': f"Vehicle capacity must not exceed {capacity_value} {unit}"
        }

    def convert_time_window_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert time window constraint to mathematical format"""
        customer_id = params['customer_id']

        if 'start_hour' in params:  # Time window constraint
            start_time = self._convert_to_minutes(
                params['start_hour'],
                params.get('start_minute', '0'),
                params.get('start_period', '')
            )
            end_time = self._convert_to_minutes(
                params['end_hour'],
                params.get('end_minute', '0'),
                params.get('end_period', '')
            )

            return {
                'type': 'time_window',
                'customer': customer_id,
                'mathematical_form': f"{start_time} <= arrival_time_{customer_id} <= {end_time}",
                'solver_format': {
                    'constraint_type': 'bound',
                    'variable': f'arrival_time_{customer_id}',
                    'lower_bound': start_time,
                    'upper_bound': end_time
                },
                'description': f"Customer {customer_id} must be visited between {start_time // 60:02d}:{start_time % 60:02d} and {end_time // 60:02d}:{end_time % 60:02d}"
            }
        else:  # Before constraint
            deadline = self._convert_to_minutes(
                params['hour'],
                params.get('minute', '0'),
                params.get('period', '')
            )

            return {
                'type': 'deadline',
                'customer': customer_id,
                'mathematical_form': f"arrival_time_{customer_id} <= {deadline}",
                'solver_format': {
                    'constraint_type': 'linear',
                    'coefficients': {f'arrival_time_{customer_id}': 1},
                    'operator': '<=',
                    'rhs': deadline
                },
                'description': f"Customer {customer_id} must be visited before {deadline // 60:02d}:{deadline % 60:02d}"
            }

    def convert_distance_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert distance constraint to mathematical format"""
        distance_value = float(params['distance_value'])
        unit = params.get('unit', 'km')

        return {
            'type': 'distance',
            'mathematical_form': f"sum(distance_ij * x_ij for all i,j) <= {distance_value}",
            'solver_format': {
                'constraint_type': 'linear',
                'coefficients': 'distance_matrix',
                'operator': '<=',
                'rhs': distance_value,
                'variables': 'route_variables'
            },
            'unit': unit,
            'description': f"Total route distance must not exceed {distance_value} {unit}"
        }

    def convert_working_hours_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert working hours constraint to mathematical format"""
        max_hours = float(params['hours'])
        max_minutes = max_hours * 60

        return {
            'type': 'working_hours',
            'mathematical_form': f"total_working_time <= {max_minutes}",
            'solver_format': {
                'constraint_type': 'linear',
                'coefficients': {'working_time': 1},
                'operator': '<=',
                'rhs': max_minutes
            },
            'description': f"Driver cannot work more than {max_hours} hours ({max_minutes} minutes)"
        }

    def convert_vehicle_restriction_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert vehicle restriction constraint to mathematical format"""
        vehicle_id = params['vehicle_id']
        location_id = params['location_id']

        return {
            'type': 'vehicle_restriction',
            'vehicle': vehicle_id,
            'location': location_id,
            'mathematical_form': f"x_{vehicle_id}_{location_id} = 0",
            'solver_format': {
                'constraint_type': 'binary_restriction',
                'variable': f'x_{vehicle_id}_{location_id}',
                'value': 0
            },
            'description': f"Vehicle {vehicle_id} cannot visit location {location_id}"
        }

    def convert_priority_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert priority constraint to mathematical format"""
        customer_id = params['customer_id']

        return {
            'type': 'priority',
            'customer': customer_id,
            'mathematical_form': f"priority_weight_{customer_id} = 10",
            'solver_format': {
                'constraint_type': 'objective_weight',
                'variable': f'priority_weight_{customer_id}',
                'weight': 10
            },
            'description': f"Customer {customer_id} has high priority"
        }

    def convert_vehicle_count_constraint(self, params: Dict, context: Dict) -> Dict:
        """Convert vehicle count constraint to mathematical format"""
        if 'min_vehicles' in params:
            min_vehicles = int(params['min_vehicles'])
            return {
                'type': 'min_vehicles',
                'mathematical_form': f"sum(vehicle_used_k for all k) >= {min_vehicles}",
                'solver_format': {
                    'constraint_type': 'linear',
                    'coefficients': 'vehicle_usage_vector',
                    'operator': '>=',
                    'rhs': min_vehicles
                },
                'min_vehicles': min_vehicles,
                'description': f"At least {min_vehicles} vehicle(s) must be used"
            }
        else:  # max_vehicles
            max_vehicles = int(params['max_vehicles'])
            return {
                'type': 'max_vehicles',
                'mathematical_form': f"sum(vehicle_used_k for all k) <= {max_vehicles}",
                'solver_format': {
                    'constraint_type': 'linear',
                    'coefficients': 'vehicle_usage_vector',
                    'operator': '<=',
                    'rhs': max_vehicles
                },
                'max_vehicles': max_vehicles,
                'description': f"At most {max_vehicles} vehicle(s) can be used"
            }

    def _convert_to_minutes(self, hour: str, minute: str = '0', period: str = '') -> int:
        """Convert time to minutes from midnight"""
        h = int(hour)
        m = int(minute) if minute else 0

        if period.upper() == 'PM' and h != 12:
            h += 12
        elif period.upper() == 'AM' and h == 12:
            h = 0

        return h * 60 + m