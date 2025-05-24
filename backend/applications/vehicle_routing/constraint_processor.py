# backend/applications/vehicle_routing/constraint_processor.py

from typing import Dict, List, Optional, Tuple
import json
from .constraint_patterns import VRPConstraintMatcher, ConstraintConverter
from .llm_parser import LLMConstraintParser, ConstraintValidator


class ConstraintProcessor:
    """
    Main constraint processor that orchestrates the entire pipeline:
    1. Pattern matching
    2. LLM fallback parsing
    3. Validation
    4. Mathematical conversion
    """

    def __init__(self, use_llm: bool = False, llm_api_key: Optional[str] = None):
        self.constraint_matcher = VRPConstraintMatcher()
        self.constraint_converter = ConstraintConverter()
        self.llm_parser = LLMConstraintParser(llm_api_key) if use_llm else None
        self.processed_constraints = []

    def process_constraint(self, prompt: str, problem_context: Dict) -> Dict:
        """
        Main pipeline for processing natural language constraints

        Args:
            prompt: Natural language constraint description
            problem_context: Problem data for validation

        Returns:
            Dict with processing results
        """

        result = {
            'success': False,
            'constraint': None,
            'method': None,
            'errors': [],
            'warnings': []
        }

        try:
            # Step 1: Clean and normalize the prompt
            normalized_prompt = self._normalize_prompt(prompt)

            # Step 2: Try pattern matching first
            pattern_result = self.constraint_matcher.match_constraint(normalized_prompt)

            if pattern_result:
                constraint_type, match_info = pattern_result

                # Convert using pattern-based converter
                converter_func = getattr(self.constraint_converter, match_info['conversion_function'])
                mathematical_constraint = converter_func(
                    match_info['parameters'],
                    problem_context
                )

                processed_constraint = {
                    'original_prompt': prompt,
                    'normalized_prompt': normalized_prompt,
                    'constraint_type': constraint_type,
                    'parameters': match_info['parameters'],
                    'mathematical_format': mathematical_constraint,
                    'parsing_method': 'pattern_matching',
                    'confidence': 0.95
                }

                result['method'] = 'pattern_matching'

            elif self.llm_parser:
                # Step 3: Use LLM as fallback
                llm_result = self.llm_parser.parse_constraint(prompt, problem_context)

                if llm_result and not llm_result.get('requires_manual_review', False):
                    processed_constraint = llm_result
                    processed_constraint['original_prompt'] = prompt
                    processed_constraint['normalized_prompt'] = normalized_prompt
                    result['method'] = 'llm_parsing'
                else:
                    result['errors'].append('LLM could not parse constraint reliably')
                    return result

            else:
                result['errors'].append('Pattern not recognized and LLM not available')
                return result

            # Step 4: Validate constraint
            validator = ConstraintValidator(problem_context)
            validation_result = validator.validate_constraint(processed_constraint)
            processed_constraint['validation'] = validation_result

            if not validation_result['is_valid']:
                result['errors'].extend(validation_result['errors'])
                result['warnings'].extend(validation_result['warnings'])
            else:
                result['warnings'].extend(validation_result.get('warnings', []))

            # Step 5: Success!
            result['success'] = True
            result['constraint'] = processed_constraint

            return result

        except Exception as e:
            result['errors'].append(f'Processing failed: {str(e)}')
            return result

    def process_multiple_constraints(self, constraints: List[str], problem_context: Dict) -> Dict:
        """Process multiple constraints and detect conflicts"""

        results = {
            'successful': [],
            'failed': [],
            'conflicts': [],
            'summary': {}
        }

        processed_constraints = []

        # Process each constraint
        for i, constraint_prompt in enumerate(constraints):
            result = self.process_constraint(constraint_prompt, problem_context)

            if result['success']:
                results['successful'].append({
                    'index': i,
                    'prompt': constraint_prompt,
                    'constraint': result['constraint'],
                    'method': result['method']
                })
                processed_constraints.append(result['constraint'])
            else:
                results['failed'].append({
                    'index': i,
                    'prompt': constraint_prompt,
                    'errors': result['errors']
                })

        # Detect conflicts between constraints
        results['conflicts'] = self._detect_conflicts(processed_constraints)

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    def _normalize_prompt(self, prompt: str) -> str:
        """Clean and normalize the prompt"""
        # Remove extra whitespace
        normalized = ' '.join(prompt.split())

        # Convert to lowercase for pattern matching
        normalized = normalized.lower()

        # Remove common filler words that don't affect meaning
        filler_words = ['please', 'kindly', 'can you', 'i want', 'i need']
        for filler in filler_words:
            normalized = normalized.replace(filler, '')

        # Clean up multiple spaces
        normalized = ' '.join(normalized.split())

        return normalized.strip()

    def _detect_conflicts(self, constraints: List[Dict]) -> List[Dict]:
        """Detect conflicts between processed constraints"""
        conflicts = []

        # Group constraints by type
        by_type = {}
        for constraint in constraints:
            constraint_type = constraint.get('constraint_type', 'unknown')
            if constraint_type not in by_type:
                by_type[constraint_type] = []
            by_type[constraint_type].append(constraint)

        # Check for conflicting capacity constraints
        if 'capacity' in by_type and len(by_type['capacity']) > 1:
            capacities = []
            for constraint in by_type['capacity']:
                capacity = constraint.get('parameters', {}).get('capacity_value')
                if capacity:
                    capacities.append(float(capacity))

            if len(set(capacities)) > 1:
                conflicts.append({
                    'type': 'conflicting_capacities',
                    'message': f'Multiple different capacity values: {capacities}',
                    'severity': 'high',
                    'affected_constraints': by_type['capacity']
                })

        # Check for conflicting time windows for same customer
        if 'time_window' in by_type:
            customer_windows = {}
            for constraint in by_type['time_window']:
                customer = constraint.get('parameters', {}).get('customer_id')
                if customer:
                    if customer not in customer_windows:
                        customer_windows[customer] = []
                    customer_windows[customer].append(constraint)

            for customer, windows in customer_windows.items():
                if len(windows) > 1:
                    conflicts.append({
                        'type': 'conflicting_time_windows',
                        'message': f'Multiple time windows for customer {customer}',
                        'severity': 'medium',
                        'customer': customer,
                        'affected_constraints': windows
                    })

        # Check for impossible vehicle restrictions
        if 'vehicle_restriction' in by_type:
            location_restrictions = {}
            for constraint in by_type['vehicle_restriction']:
                params = constraint.get('parameters', {})
                location = params.get('location', params.get('location_id'))
                vehicle = params.get('vehicle', params.get('vehicle_id'))

                if location:
                    if location not in location_restrictions:
                        location_restrictions[location] = {'forbidden': [], 'exclusive': []}

                    if constraint.get('constraint_type') == 'vehicle_location_forbidden':
                        location_restrictions[location]['forbidden'].append(vehicle)
                    else:
                        location_restrictions[location]['exclusive'].append(vehicle)

            for location, restrictions in location_restrictions.items():
                if restrictions['forbidden'] and restrictions['exclusive']:
                    conflicts.append({
                        'type': 'impossible_vehicle_restriction',
                        'message': f'Location {location} has both forbidden and exclusive vehicle restrictions',
                        'severity': 'high',
                        'location': location,
                        'details': restrictions
                    })

        return conflicts

    def _generate_summary(self, results: Dict) -> Dict:
        """Generate processing summary"""
        total = len(results['successful']) + len(results['failed'])

        summary = {
            'total_constraints': total,
            'successful': len(results['successful']),
            'failed': len(results['failed']),
            'success_rate': len(results['successful']) / total if total > 0 else 0,
            'conflicts_found': len(results['conflicts']),
            'by_type': {},
            'by_method': {}
        }

        # Count by constraint type and parsing method
        for item in results['successful']:
            constraint = item['constraint']
            constraint_type = constraint.get('constraint_type', 'unknown')
            method = item.get('method', 'unknown')

            summary['by_type'][constraint_type] = summary['by_type'].get(constraint_type, 0) + 1
            summary['by_method'][method] = summary['by_method'].get(method, 0) + 1

        return summary

    def export_constraints_for_solver(self, constraints: List[Dict], solver_type: str = 'pulp') -> Dict:
        """
        Export processed constraints in format suitable for different solvers

        Args:
            constraints: List of processed constraints
            solver_type: 'pulp', 'ortools', 'gurobi', etc.

        Returns:
            Dict with solver-specific constraint format
        """

        if solver_type.lower() == 'pulp':
            return self._export_for_pulp(constraints)
        elif solver_type.lower() == 'ortools':
            return self._export_for_ortools(constraints)
        else:
            return self._export_generic(constraints)

    def _export_for_pulp(self, constraints: List[Dict]) -> Dict:
        """Export constraints for PuLP solver"""
        pulp_constraints = {
            'capacity_constraints': [],
            'time_constraints': [],
            'distance_constraints': [],
            'vehicle_restrictions': [],
            'vehicle_count_constraints': [],
            'custom_constraints': []
        }

        for constraint in constraints:
            constraint_type = constraint.get('constraint_type')
            math_format = constraint.get('mathematical_format', {})

            if constraint_type in ['vehicle_capacity_max', 'capacity']:
                pulp_constraints['capacity_constraints'].append({
                    'type': 'capacity',
                    'max_capacity': math_format.get('solver_format', {}).get('rhs', 100),
                    'description': math_format.get('description', ''),
                    'original_prompt': constraint.get('original_prompt', '')
                })

            elif constraint_type in ['time_window', 'delivery_before']:
                pulp_constraints['time_constraints'].append({
                    'type': constraint_type,
                    'customer': constraint.get('parameters', {}).get('customer_id'),
                    'time_bounds': math_format.get('solver_format', {}),
                    'description': math_format.get('description', ''),
                    'original_prompt': constraint.get('original_prompt', '')
                })

            elif constraint_type in ['max_route_distance', 'distance']:
                pulp_constraints['distance_constraints'].append({
                    'type': 'max_distance',
                    'max_distance': math_format.get('solver_format', {}).get('rhs', 1000),
                    'description': math_format.get('description', ''),
                    'original_prompt': constraint.get('original_prompt', '')
                })

            elif constraint_type in ['vehicle_location_forbidden', 'vehicle_location_exclusive']:
                pulp_constraints['vehicle_restrictions'].append({
                    'type': constraint_type,
                    'vehicle': constraint.get('parameters', {}).get('vehicle_id'),
                    'location': constraint.get('parameters', {}).get('location_id'),
                    'description': math_format.get('description', ''),
                    'original_prompt': constraint.get('original_prompt', '')
                })

            elif constraint_type in ['min_vehicles', 'max_vehicles']:
                pulp_constraints['vehicle_count_constraints'].append({
                    'type': constraint_type,
                    'count': math_format.get('solver_format', {}).get('rhs', 1),
                    'operator': math_format.get('solver_format', {}).get('operator', '>='),
                    'description': math_format.get('description', ''),
                    'original_prompt': constraint.get('original_prompt', '')
                })

            else:
                pulp_constraints['custom_constraints'].append({
                    'type': constraint_type,
                    'parameters': constraint.get('parameters', {}),
                    'mathematical_form': math_format.get('mathematical_form', ''),
                    'description': math_format.get('description', ''),
                    'original_prompt': constraint.get('original_prompt', '')
                })

        return pulp_constraints

    def _export_for_ortools(self, constraints: List[Dict]) -> Dict:
        """Export constraints for OR-Tools solver (from previous artifact)"""
        # This would use the constraint_integration.py code I provided earlier
        return {'ortools_format': 'See constraint_integration.py'}

    def _export_generic(self, constraints: List[Dict]) -> Dict:
        """Export constraints in generic mathematical format"""
        return {
            'mathematical_constraints': [
                {
                    'original_prompt': c.get('original_prompt', ''),
                    'constraint_type': c.get('constraint_type', ''),
                    'mathematical_form': c.get('mathematical_format', {}).get('mathematical_form', ''),
                    'parameters': c.get('parameters', {}),
                    'description': c.get('mathematical_format', {}).get('description', '')
                }
                for c in constraints
            ]
        }