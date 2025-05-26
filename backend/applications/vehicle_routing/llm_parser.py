# backend/applications/vehicle_routing/llm_parser.py

import json
import re
import os
from typing import Dict, Optional, List

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


class LLMConstraintParser:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._get_api_key()
        self.client = None
        
        # Debug logging
        print(f"[LLM Debug] OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
        print(f"[LLM Debug] API key found: {bool(self.api_key)}")
        if self.api_key:
            print(f"[LLM Debug] API key length: {len(self.api_key)}")
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print(f"[LLM Debug] OpenAI client initialized successfully")
            except Exception as e:
                print(f"[LLM Debug] Failed to initialize OpenAI client: {e}")
        else:
            if not OPENAI_AVAILABLE:
                print(f"[LLM Debug] OpenAI package not available")
            if not self.api_key:
                print(f"[LLM Debug] No API key found")
                
        self.system_prompt = self._create_system_prompt()

    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from various sources"""
        print(f"[LLM Debug] Checking for API key...")
        print(f"[LLM Debug] Environment variables available: {list(os.environ.keys())}")
        
        # Try environment variable first
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            print(f"[LLM Debug] Found API key in environment variable (length: {len(api_key)})")
            return api_key
        else:
            print(f"[LLM Debug] No OPENAI_API_KEY in environment variables")
            
        # Try streamlit secrets (if available)
        try:
            import streamlit as st
            # Try both formats of the API key in secrets
            if hasattr(st, 'secrets'):
                # Try the nested format first
                if 'openai' in st.secrets and 'api_key' in st.secrets['openai']:
                    api_key = st.secrets['openai']['api_key']
                    print(f"[LLM Debug] Found API key in streamlit secrets (openai.api_key)")
                    return api_key
                # Try the direct format
                elif 'OPENAI_API_KEY' in st.secrets:
                    api_key = st.secrets['OPENAI_API_KEY']
                    print(f"[LLM Debug] Found API key in streamlit secrets (OPENAI_API_KEY)")
                    return api_key
                else:
                    print(f"[LLM Debug] Available secrets keys: {list(st.secrets.keys())}")
                    if 'openai' in st.secrets:
                        print(f"[LLM Debug] Available openai secrets: {list(st.secrets['openai'].keys())}")
            else:
                print(f"[LLM Debug] No streamlit secrets available")
        except Exception as e:
            print(f"[LLM Debug] Error accessing streamlit secrets: {e}")
            
        print(f"[LLM Debug] No API key found in any source")
        return None

    def _create_system_prompt(self) -> str:
        return """
You are a constraint parser for Vehicle Routing Problems (VRP). Your task is to parse natural language constraints and convert them into structured format.

Given a natural language constraint, extract:
1. constraint_type: One of [capacity, time_window, distance, working_hours, vehicle_restriction, priority, vehicle_count, custom]
2. parameters: Key-value pairs of constraint parameters
3. mathematical_description: How this constraint would be expressed mathematically
4. entities: What entities (vehicles, customers, locations) are involved

Output format (JSON):
{
    "constraint_type": "string",
    "parameters": {
        "key": "value"
    },
    "entities": {
        "vehicles": ["list of vehicle IDs"],
        "customers": ["list of customer IDs"],
        "locations": ["list of location IDs"]
    },
    "mathematical_description": "string describing the mathematical constraint",
    "confidence": 0.95,
    "interpretation": "human-readable interpretation of the constraint"
}

Examples:

Input: "Each truck can carry maximum 500kg"
Output: {
    "constraint_type": "capacity",
    "parameters": {
        "max_capacity": 500,
        "unit": "kg",
        "applies_to": "all_vehicles"
    },
    "entities": {
        "vehicles": ["all"],
        "customers": [],
        "locations": []
    },
    "mathematical_description": "sum(demand_j * x_ij) <= 500 for each vehicle i",
    "confidence": 0.98,
    "interpretation": "Every vehicle has a maximum carrying capacity of 500 kilograms"
}

Input: "mimimum 2 vehicles should be used"
Output: {
    "constraint_type": "vehicle_count",
    "parameters": {
        "min_vehicles": 2,
        "constraint_direction": "minimum"
    },
    "entities": {
        "vehicles": ["all"],
        "customers": [],
        "locations": []
    },
    "mathematical_description": "sum(vehicle_used_k for all k) >= 2",
    "confidence": 0.95,
    "interpretation": "At least 2 vehicles must be used (handles typo in 'mimimum')"
}

Be precise and handle ambiguous cases by asking for clarification in the interpretation field.
Handle typos and informal language gracefully.
"""

    def parse_constraint(self, prompt: str, context: Dict = None) -> Optional[Dict]:
        """Parse constraint using LLM when pattern matching fails"""
        print(f"[LLM Debug] Starting constraint parsing for: '{prompt}'")

        if not OPENAI_AVAILABLE:
            print("[LLM Debug] OpenAI package not available, using fallback parsing")
            return self._fallback_parse(prompt)

        if not self.client:
            print("[LLM Debug] OpenAI client not initialized (missing API key), using fallback parsing")
            return self._fallback_parse(prompt)

        try:
            print("[LLM Debug] Attempting LLM parsing...")
            # Prepare context information
            context_info = ""
            if context:
                context_info = f"\nContext: {json.dumps(context, indent=2)}"

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Parse this constraint: '{prompt}'{context_info}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            # Parse the JSON response
            content = response.choices[0].message.content.strip()
            print(f"[LLM Debug] Raw OpenAI response: {content}")
            
            # Try to extract JSON if it's wrapped in code blocks
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result = json.loads(content)
            result['parsing_method'] = 'llm'
            
            # Ensure required fields exist
            if 'confidence' not in result:
                result['confidence'] = 0.8
                
            print(f"[LLM Debug] LLM parsing successful! Type: {result.get('constraint_type')}")
            return result

        except Exception as e:
            print(f"[LLM Debug] LLM parsing failed: {e}")
            return self._fallback_parse(prompt)

    def _fallback_parse(self, prompt: str) -> Dict:
        """Simple fallback parsing when LLM is not available"""
        print(f"[LLM Debug] Using fallback parsing for: '{prompt}'")
        
        # Try some basic pattern matching for common cases
        fallback_result = self._basic_fallback_parsing(prompt)
        
        if fallback_result['constraint_type'] != 'custom':
            return fallback_result
        
        return {
            "constraint_type": "custom",
            "parameters": {
                "raw_constraint": prompt
            },
            "entities": {
                "vehicles": [],
                "customers": [],
                "locations": []
            },
            "mathematical_description": "Custom constraint requiring manual interpretation",
            "confidence": 0.3,
            "interpretation": f"Could not automatically parse: '{prompt}'. Manual review required.",
            "parsing_method": "fallback",
            "requires_manual_review": True
        }

    def _basic_fallback_parsing(self, prompt: str) -> Dict:
        """Basic fallback parsing for common patterns"""
        prompt_lower = prompt.lower()
        
        # Vehicle count patterns
        vehicle_count_patterns = [
            (r'm(?:in|im)(?:imum)?\s+(\d+)\s+vehicles?\s+should\s+be\s+used', 'min_vehicles'),
            (r'need\s+(?:at\s+least\s+)?(\d+)\s+vehicles?', 'min_vehicles'),
            (r'use\s+at\s+least\s+(\d+)\s+vehicles?', 'min_vehicles'),
            (r'max(?:imum)?\s+(\d+)\s+vehicles?\s+should\s+be\s+used', 'max_vehicles'),
            (r'use\s+(?:at\s+most\s+)?(\d+)\s+vehicles?', 'max_vehicles')
        ]
        
        # Generic vehicle reduction patterns (for vague constraints)
        vehicle_reduction_patterns = [
            r'use\s+fewer\s+vehicles?(?:\s+only)?',
            r'use\s+least\s+(?:number\s+of\s+)?vehicles?',
            r'use\s+(?:the\s+)?minimum\s+(?:number\s+of\s+)?vehicles?',
            r'reduce\s+(?:the\s+)?(?:number\s+of\s+)?vehicles?',
            r'minimize\s+(?:the\s+)?(?:number\s+of\s+)?vehicles?',
            r'less\s+vehicles?',
            r'minimum\s+vehicles?(?:\s+only)?',
            r'fewest\s+vehicles?'
        ]
        
        for pattern in vehicle_reduction_patterns:
            if re.search(pattern, prompt_lower):
                return {
                    "constraint_type": "vehicle_count",
                    "parameters": {
                        "constraint_direction": "minimize",
                        "objective": "reduce_vehicle_count"
                    },
                    "entities": {
                        "vehicles": ["all"],
                        "customers": [],
                        "locations": []
                    },
                    "mathematical_description": "minimize sum(vehicle_used_k for all k)",
                    "confidence": 0.75,
                    "interpretation": "Minimize the number of vehicles used in the solution",
                    "parsing_method": "fallback_pattern"
                }
        
        for pattern, constraint_subtype in vehicle_count_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                count = int(match.group(1))
                return {
                    "constraint_type": "vehicle_count",
                    "parameters": {
                        constraint_subtype.replace('_vehicles', ''): count,
                        "constraint_direction": constraint_subtype.split('_')[0]
                    },
                    "entities": {
                        "vehicles": ["all"],
                        "customers": [],
                        "locations": []
                    },
                    "mathematical_description": f"sum(vehicle_used_k for all k) {'>==' if 'min' in constraint_subtype else '<='} {count}",
                    "confidence": 0.85,
                    "interpretation": f"{'At least' if 'min' in constraint_subtype else 'At most'} {count} vehicles must be used",
                    "parsing_method": "fallback_pattern"
                }
        
        # Capacity patterns
        capacity_patterns = [
            r'at\s+max(?:imum)?\s+(\d+(?:\.\d+)?)\s*(\w+)?\s+capacity\s+should\s+be\s+used',
            r'vehicle\s+capacity\s+(?:should\s+)?(?:not\s+)?(?:exceed|be\s+(?:less\s+than|under|below|at\s+most))\s+(\d+(?:\.\d+)?)\s*(\w+)?',
            r'(?:each\s+)?vehicle\s+can\s+carry\s+(?:at\s+most\s+|maximum\s+)?(\d+(?:\.\d+)?)\s*(\w+)?'
        ]
        
        for pattern in capacity_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                capacity = float(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else "units"
                return {
                    "constraint_type": "capacity",
                    "parameters": {
                        "max_capacity": capacity,
                        "unit": unit,
                        "applies_to": "all_vehicles"
                    },
                    "entities": {
                        "vehicles": ["all"],
                        "customers": [],
                        "locations": []
                    },
                    "mathematical_description": f"sum(demand_j * x_ij) <= {capacity} for each vehicle i",
                    "confidence": 0.85,
                    "interpretation": f"Each vehicle can carry at most {capacity} {unit}",
                    "parsing_method": "fallback_pattern"
                }
        
        # If no patterns match, return custom
        return {
            "constraint_type": "custom",
            "parameters": {"raw_constraint": prompt},
            "entities": {"vehicles": [], "customers": [], "locations": []},
            "mathematical_description": "Custom constraint",
            "confidence": 0.3,
            "interpretation": "Could not parse automatically",
            "parsing_method": "fallback"
        }

    def is_available(self) -> bool:
        """Check if LLM parsing is available"""
        return OPENAI_AVAILABLE and self.client is not None 


class ConstraintValidator:
    """Validates parsed constraints for consistency and feasibility"""
    
    def __init__(self, problem_context: Dict = None):
        self.problem_context = problem_context or {}
        
    def validate_constraint(self, constraint: Dict) -> Dict:
        """
        Validate a parsed constraint for feasibility and consistency
        Returns validation result with suggestions
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
            "modified_constraint": constraint.copy()
        }
        
        constraint_type = constraint.get('constraint_type', 'unknown')
        parameters = constraint.get('parameters', {})
        
        # Validate based on constraint type
        if constraint_type == 'capacity':
            validation_result = self._validate_capacity_constraint(constraint, validation_result)
        elif constraint_type == 'vehicle_count':
            validation_result = self._validate_vehicle_count_constraint(constraint, validation_result)
        elif constraint_type == 'time_window':
            validation_result = self._validate_time_window_constraint(constraint, validation_result)
        elif constraint_type == 'distance':
            validation_result = self._validate_distance_constraint(constraint, validation_result)
        elif constraint_type == 'custom':
            validation_result["warnings"].append("Custom constraints require manual review")
            
        return validation_result
    
    def _validate_capacity_constraint(self, constraint: Dict, result: Dict) -> Dict:
        """Validate capacity constraints"""
        params = constraint.get('parameters', {})
        max_capacity = params.get('max_capacity', 0)
        
        if max_capacity <= 0:
            result["errors"].append("Capacity must be positive")
            result["is_valid"] = False
        
        # Check against problem context if available
        if self.problem_context.get('vehicle_capacity'):
            current_capacity = self.problem_context['vehicle_capacity']
            if max_capacity > current_capacity:
                result["warnings"].append(f"Requested capacity ({max_capacity}) exceeds current vehicle capacity ({current_capacity})")
                result["suggestions"].append("Consider adjusting vehicle specifications or constraint value")
        
        return result
    
    def _validate_vehicle_count_constraint(self, constraint: Dict, result: Dict) -> Dict:
        """Validate vehicle count constraints"""
        params = constraint.get('parameters', {})
        
        min_vehicles = params.get('min_vehicles', params.get('min', 0))
        max_vehicles = params.get('max_vehicles', params.get('max', float('inf')))
        
        if min_vehicles < 0:
            result["errors"].append("Minimum vehicle count cannot be negative")
            result["is_valid"] = False
            
        if max_vehicles < min_vehicles:
            result["errors"].append("Maximum vehicle count cannot be less than minimum")
            result["is_valid"] = False
        
        # Check against problem context
        if self.problem_context.get('vehicle_count'):
            available_vehicles = self.problem_context['vehicle_count']
            if min_vehicles > available_vehicles:
                result["warnings"].append(f"Requested minimum vehicles ({min_vehicles}) exceeds available vehicles ({available_vehicles})")
                result["suggestions"].append("Increase vehicle fleet size or reduce minimum requirement")
        
        return result
    
    def _validate_time_window_constraint(self, constraint: Dict, result: Dict) -> Dict:
        """Validate time window constraints"""
        params = constraint.get('parameters', {})
        
        start_time = params.get('start_time')
        end_time = params.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                result["errors"].append("Start time must be before end time")
                result["is_valid"] = False
        
        return result
    
    def _validate_distance_constraint(self, constraint: Dict, result: Dict) -> Dict:
        """Validate distance constraints"""
        params = constraint.get('parameters', {})
        max_distance = params.get('max_distance', params.get('distance', 0))
        
        if max_distance <= 0:
            result["warnings"].append("Distance constraint should be positive")
            result["suggestions"].append("Verify distance units and values")
        
        return result
    
    def validate_constraint_set(self, constraints: List[Dict]) -> Dict:
        """Validate a set of constraints for conflicts"""
        overall_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": [],
            "individual_results": []
        }
        
        # Validate each constraint individually
        for i, constraint in enumerate(constraints):
            individual_result = self.validate_constraint(constraint)
            individual_result["constraint_index"] = i
            overall_result["individual_results"].append(individual_result)
            
            if not individual_result["is_valid"]:
                overall_result["is_valid"] = False
                overall_result["errors"].extend(individual_result["errors"])
            
            overall_result["warnings"].extend(individual_result["warnings"])
            overall_result["suggestions"].extend(individual_result["suggestions"])
        
        # Check for conflicts between constraints
        overall_result = self._check_constraint_conflicts(constraints, overall_result)
        
        return overall_result
    
    def _check_constraint_conflicts(self, constraints: List[Dict], result: Dict) -> Dict:
        """Check for conflicts between multiple constraints"""
        # Example: conflicting capacity requirements, impossible vehicle counts, etc.
        capacity_constraints = [c for c in constraints if c.get('constraint_type') == 'capacity']
        vehicle_count_constraints = [c for c in constraints if c.get('constraint_type') == 'vehicle_count']
        
        # Check capacity conflicts
        if len(capacity_constraints) > 1:
            capacities = [c.get('parameters', {}).get('max_capacity', 0) for c in capacity_constraints]
            if len(set(capacities)) > 1:
                result["warnings"].append("Multiple different capacity constraints detected")
                result["suggestions"].append("Consider consolidating capacity requirements")
        
        # Check vehicle count conflicts
        min_vehicles = []
        max_vehicles = []
        for vc in vehicle_count_constraints:
            params = vc.get('parameters', {})
            if 'min_vehicles' in params or 'min' in params:
                min_vehicles.append(params.get('min_vehicles', params.get('min', 0)))
            if 'max_vehicles' in params or 'max' in params:
                max_vehicles.append(params.get('max_vehicles', params.get('max', float('inf'))))
        
        if min_vehicles and max_vehicles:
            max_min = max(min_vehicles)
            min_max = min(max_vehicles)
            if max_min > min_max:
                result["errors"].append(f"Conflicting vehicle count constraints: min {max_min} > max {min_max}")
                result["is_valid"] = False
        
        return result 