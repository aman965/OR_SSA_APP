#!/usr/bin/env python3
"""
Enhanced Constraint Parser for Complex VRP Constraints
Handles advanced routing constraints like node separation, grouping, and multi-part constraints
"""

import json
import re
import os
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None


@dataclass
class ConstraintEntity:
    """Represents an entity in a constraint (node, vehicle, route)"""
    type: str  # 'node', 'vehicle', 'route', 'location'
    id: str    # identifier
    properties: Dict = None


@dataclass
class ParsedConstraint:
    """Enhanced constraint representation"""
    constraint_type: str
    subtype: str = None
    parameters: Dict = None
    entities: List[ConstraintEntity] = None
    mathematical_description: str = ""
    confidence: float = 0.0
    interpretation: str = ""
    parsing_method: str = ""
    complexity_level: str = "simple"  # simple, medium, complex
    requires_preprocessing: bool = False


class EnhancedConstraintParser:
    """Enhanced parser for complex VRP constraints"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._get_api_key()
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print(f"[Enhanced Parser] OpenAI client initialized successfully")
            except Exception as e:
                print(f"[Enhanced Parser] Failed to initialize OpenAI client: {e}")
        
        self.system_prompt = self._create_enhanced_system_prompt()
        
        # Define constraint patterns for complex routing constraints
        self.constraint_patterns = {
            'node_separation': [
                r'node\s+(\d+)\s+and\s+node\s+(\d+)\s+should\s+(?:not\s+be\s+served\s+together|be\s+on\s+different\s+routes)',
                r'customer\s+(\d+)\s+and\s+customer\s+(\d+)\s+(?:cannot\s+be\s+on\s+same\s+route|must\s+be\s+separated)',
                r'separate\s+node\s+(\d+)\s+(?:and|from)\s+node\s+(\d+)',
                r'(?:node|customer)\s+(\d+)\s+(?:and|,)\s+(?:node|customer)\s+(\d+)\s+(?:should\s+)?(?:not\s+be\s+served\s+together|be\s+on\s+different\s+routes)'
            ],
            'node_grouping': [
                r'node\s+(\d+)\s+and\s+node\s+(\d+)\s+should\s+be\s+served\s+together',
                r'customer\s+(\d+)\s+and\s+customer\s+(\d+)\s+(?:must\s+be\s+on\s+same\s+route|should\s+be\s+grouped)',
                r'group\s+node\s+(\d+)\s+(?:and|with)\s+node\s+(\d+)',
                r'(?:node|customer)\s+(\d+)\s+(?:and|,)\s+(?:node|customer)\s+(\d+)\s+(?:should\s+)?(?:be\s+served\s+together|be\s+on\s+same\s+route)'
            ],
            'vehicle_assignment': [
                r'node\s+(\d+)\s+should\s+be\s+served\s+by\s+vehicle\s+(\d+)',
                r'assign\s+(?:node|customer)\s+(\d+)\s+to\s+vehicle\s+(\d+)',
                r'vehicle\s+(\d+)\s+(?:must\s+serve|should\s+visit)\s+(?:node|customer)\s+(\d+)'
            ],
            'route_constraints': [
                r'route\s+(\d+)\s+should\s+(?:not\s+)?(?:exceed|be\s+longer\s+than)\s+(\d+(?:\.\d+)?)\s*(\w+)?',
                r'maximum\s+route\s+(?:length|distance)\s+(?:should\s+be\s+)?(\d+(?:\.\d+)?)\s*(\w+)?',
                r'each\s+route\s+should\s+(?:not\s+)?(?:exceed|be\s+longer\s+than)\s+(\d+(?:\.\d+)?)\s*(\w+)?'
            ],
            'priority_constraints': [
                r'(?:node|customer)\s+(\d+)\s+(?:has\s+)?(?:high|low|medium)\s+priority',
                r'prioritize\s+(?:node|customer)\s+(\d+)',
                r'(?:node|customer)\s+(\d+)\s+should\s+be\s+served\s+(?:first|last|early)'
            ],
            'multi_part_constraints': [
                r'minimum\s+(\d+)\s+vehicles?\s+should\s+be\s+used.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+node\s+(\d+)\s+should\s+be\s+served\s+together',
                r'use\s+at\s+least\s+(\d+)\s+vehicles?.*(?:and|also|additionally).*(?:node|customer)\s+(\d+)\s+(?:and|,)\s+(?:node|customer)\s+(\d+)\s+(?:should\s+)?(?:not\s+be\s+served\s+together|be\s+on\s+different\s+routes)',
                # Enhanced patterns for better matching
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+(?:served\s+together|(?:in|on)\s+(?:the\s+)?same\s+route)',
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+(?:not\s+be\s+served\s+together|be\s+(?:in|on)\s+different\s+routes)',
                r'(?:use|employ)\s+(?:at\s+least|minimum)\s+(\d+)\s+vehicles?.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+(?:served\s+together|(?:in|on)\s+(?:the\s+)?same\s+route)',
                r'(?:use|employ)\s+(?:at\s+least|minimum)\s+(\d+)\s+vehicles?.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+(?:not\s+be\s+served\s+together|be\s+(?:in|on)\s+different\s+routes)',
                # Additional patterns for "together in a route" variations
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used.*(?:and|also|additionally).*nodes?\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+together\s+in\s+a?\s+route',
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+node\s+(\d+)\s+should\s+be\s+together\s+in\s+a?\s+route',
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used.*(?:and|also|additionally).*node\s+(\d+)\s+and\s+node\s+(\d+)\s+should\s+be\s+(?:together|grouped)\s+(?:in|on)\s+(?:a\s+|the\s+)?(?:same\s+)?route',
                # New patterns for "covered under same route" variations with flexible whitespace
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used[\s\S]*?node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+covered\s+under\s+(?:the\s+)?same\s+route',
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used[\s\S]*?node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+(?:covered|handled|managed)\s+(?:under|by)\s+(?:the\s+)?same\s+route',
                # Most flexible pattern that handles line breaks and any whitespace
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used[\s\S]*?node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+covered\s+under\s+(?:the\s+)?same\s+route',
                # NEW PATTERN: "together in same route" (without "a")
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used[\s\S]*?nodes?\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+together\s+in\s+same\s+route',
                # Additional flexible patterns for "together in same route"
                r'(?:at\s+least|minimum)\s+(\d+)\s+vehicles?\s+should\s+be\s+used[\s\S]*?node\s+(\d+)\s+and\s+(?:node\s+)?(\d+)\s+should\s+be\s+together\s+in\s+(?:the\s+)?same\s+route'
            ]
        }

    def _get_api_key(self) -> Optional[str]:
        """Get OpenAI API key from various sources"""
        # Try environment variable first
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            return api_key
            
        # Try streamlit secrets
        try:
            import streamlit as st
            if hasattr(st, 'secrets'):
                if 'openai' in st.secrets and 'api_key' in st.secrets['openai']:
                    return st.secrets['openai']['api_key']
                elif 'OPENAI_API_KEY' in st.secrets:
                    return st.secrets['OPENAI_API_KEY']
        except:
            pass
            
        return None

    def _create_enhanced_system_prompt(self) -> str:
        return """
You are an advanced constraint parser for Vehicle Routing Problems (VRP). You can handle complex routing constraints including:

1. Node separation (nodes that cannot be on the same route)
2. Node grouping (nodes that must be on the same route)
3. Vehicle assignments (specific nodes assigned to specific vehicles)
4. Route constraints (distance, time, capacity limits per route)
5. Priority constraints (service order preferences)
6. Multi-part constraints (combinations of the above)

For each constraint, extract:
- constraint_type: [node_separation, node_grouping, vehicle_assignment, route_constraint, priority, vehicle_count, multi_part, custom]
- subtype: More specific classification
- parameters: All relevant parameters
- entities: Involved nodes, vehicles, routes
- mathematical_description: Mathematical formulation
- complexity_level: [simple, medium, complex]

Output JSON format:
{
    "constraint_type": "string",
    "subtype": "string",
    "parameters": {
        "key": "value"
    },
    "entities": {
        "nodes": ["list of node IDs"],
        "vehicles": ["list of vehicle IDs"],
        "routes": ["list of route IDs"]
    },
    "mathematical_description": "mathematical formulation",
    "confidence": 0.95,
    "interpretation": "human-readable interpretation",
    "complexity_level": "simple|medium|complex",
    "requires_preprocessing": false
}

Examples:

Input: "node 1 and node 4 should not be served together"
Output: {
    "constraint_type": "node_separation",
    "subtype": "pairwise_separation",
    "parameters": {
        "node_1": 1,
        "node_2": 4,
        "separation_type": "different_routes"
    },
    "entities": {
        "nodes": ["1", "4"],
        "vehicles": [],
        "routes": []
    },
    "mathematical_description": "sum(x[i,1,k] for i in nodes) + sum(x[i,4,k] for i in nodes) <= 1 for each vehicle k",
    "confidence": 0.95,
    "interpretation": "Nodes 1 and 4 must be served by different vehicles",
    "complexity_level": "medium",
    "requires_preprocessing": false
}

Input: "minimum 2 vehicles should be used. Also, node 1 and node 2 should be served together"
Output: {
    "constraint_type": "multi_part",
    "subtype": "vehicle_count_and_grouping",
    "parameters": {
        "min_vehicles": 2,
        "grouped_nodes": [1, 2],
        "grouping_type": "same_route"
    },
    "entities": {
        "nodes": ["1", "2"],
        "vehicles": ["all"],
        "routes": []
    },
    "mathematical_description": "sum(used_k for all k) >= 2 AND sum(x[i,1,k] for i in nodes) == sum(x[i,2,k] for i in nodes) for each k",
    "confidence": 0.90,
    "interpretation": "Use at least 2 vehicles and ensure nodes 1 and 2 are on the same route",
    "complexity_level": "complex",
    "requires_preprocessing": true
}

Handle typos, informal language, and ambiguous cases gracefully.
"""

    def parse_constraint(self, prompt: str, context: Dict = None) -> ParsedConstraint:
        """Parse constraint using enhanced pattern matching and LLM"""
        print(f"[Enhanced Parser] Parsing constraint: '{prompt}'")
        
        # First try pattern matching for known complex constraints
        pattern_result = self._pattern_match_constraint(prompt)
        if pattern_result and pattern_result.confidence > 0.8:
            print(f"[Enhanced Parser] High confidence pattern match: {pattern_result.constraint_type}")
            return pattern_result
        
        # If pattern matching fails or has low confidence, use LLM
        if self.client:
            llm_result = self._llm_parse_constraint(prompt, context)
            if llm_result:
                print(f"[Enhanced Parser] LLM parsing successful: {llm_result.constraint_type}")
                return llm_result
        
        # Fallback to basic parsing
        print(f"[Enhanced Parser] Using fallback parsing")
        return self._fallback_parse_constraint(prompt)

    def _pattern_match_constraint(self, prompt: str) -> Optional[ParsedConstraint]:
        """Pattern matching for complex constraints"""
        prompt_lower = prompt.lower().strip()
        
        # Check for multi-part constraints first (most complex)
        for pattern in self.constraint_patterns['multi_part_constraints']:
            # Use re.DOTALL to make . match newlines
            match = re.search(pattern, prompt_lower, re.DOTALL)
            if match:
                return self._parse_multi_part_constraint(match, prompt)
        
        # Check for node separation
        for pattern in self.constraint_patterns['node_separation']:
            match = re.search(pattern, prompt_lower, re.DOTALL)
            if match:
                return self._parse_node_separation(match, prompt)
        
        # Check for node grouping
        for pattern in self.constraint_patterns['node_grouping']:
            match = re.search(pattern, prompt_lower, re.DOTALL)
            if match:
                return self._parse_node_grouping(match, prompt)
        
        # Check for vehicle assignment
        for pattern in self.constraint_patterns['vehicle_assignment']:
            match = re.search(pattern, prompt_lower, re.DOTALL)
            if match:
                return self._parse_vehicle_assignment(match, prompt)
        
        # Check for route constraints
        for pattern in self.constraint_patterns['route_constraints']:
            match = re.search(pattern, prompt_lower, re.DOTALL)
            if match:
                return self._parse_route_constraint(match, prompt)
        
        # Check for priority constraints
        for pattern in self.constraint_patterns['priority_constraints']:
            match = re.search(pattern, prompt_lower, re.DOTALL)
            if match:
                return self._parse_priority_constraint(match, prompt)
        
        return None

    def _parse_node_separation(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse node separation constraints"""
        node1 = int(match.group(1))
        node2 = int(match.group(2))
        
        return ParsedConstraint(
            constraint_type="node_separation",
            subtype="pairwise_separation",
            parameters={
                "node_1": node1,
                "node_2": node2,
                "separation_type": "different_routes"
            },
            entities=[
                ConstraintEntity("node", str(node1)),
                ConstraintEntity("node", str(node2))
            ],
            mathematical_description=f"sum(x[i,{node1},k] for i in nodes) + sum(x[i,{node2},k] for i in nodes) <= 1 for each vehicle k",
            confidence=0.90,
            interpretation=f"Nodes {node1} and {node2} must be served by different vehicles",
            parsing_method="pattern_matching",
            complexity_level="medium",
            requires_preprocessing=False
        )

    def _parse_node_grouping(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse node grouping constraints"""
        node1 = int(match.group(1))
        node2 = int(match.group(2))
        
        return ParsedConstraint(
            constraint_type="node_grouping",
            subtype="pairwise_grouping",
            parameters={
                "node_1": node1,
                "node_2": node2,
                "grouping_type": "same_route"
            },
            entities=[
                ConstraintEntity("node", str(node1)),
                ConstraintEntity("node", str(node2))
            ],
            mathematical_description=f"sum(x[i,{node1},k] for i in nodes) == sum(x[i,{node2},k] for i in nodes) for each vehicle k",
            confidence=0.90,
            interpretation=f"Nodes {node1} and {node2} must be served by the same vehicle",
            parsing_method="pattern_matching",
            complexity_level="medium",
            requires_preprocessing=False
        )

    def _parse_vehicle_assignment(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse vehicle assignment constraints"""
        if "node" in original_prompt.lower() and "vehicle" in original_prompt.lower():
            # Extract node and vehicle numbers
            node_match = re.search(r'node\s+(\d+)', original_prompt.lower())
            vehicle_match = re.search(r'vehicle\s+(\d+)', original_prompt.lower())
            
            if node_match and vehicle_match:
                node = int(node_match.group(1))
                vehicle = int(vehicle_match.group(1))
                
                return ParsedConstraint(
                    constraint_type="vehicle_assignment",
                    subtype="fixed_assignment",
                    parameters={
                        "node": node,
                        "vehicle": vehicle,
                        "assignment_type": "mandatory"
                    },
                    entities=[
                        ConstraintEntity("node", str(node)),
                        ConstraintEntity("vehicle", str(vehicle))
                    ],
                    mathematical_description=f"sum(x[i,{node},{vehicle}] for i in nodes) == 1",
                    confidence=0.85,
                    interpretation=f"Node {node} must be served by vehicle {vehicle}",
                    parsing_method="pattern_matching",
                    complexity_level="simple",
                    requires_preprocessing=False
                )
        
        return None

    def _parse_route_constraint(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse route-level constraints"""
        distance = float(match.group(1)) if match.group(1) else 0
        unit = match.group(2) if len(match.groups()) > 1 and match.group(2) else "units"
        
        return ParsedConstraint(
            constraint_type="route_constraint",
            subtype="max_distance",
            parameters={
                "max_distance": distance,
                "unit": unit,
                "applies_to": "all_routes"
            },
            entities=[
                ConstraintEntity("route", "all")
            ],
            mathematical_description=f"sum(distance[i,j] * x[i,j,k] for i,j in edges) <= {distance} for each vehicle k",
            confidence=0.85,
            interpretation=f"Each route must not exceed {distance} {unit}",
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_priority_constraint(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse priority constraints"""
        node_match = re.search(r'(?:node|customer)\s+(\d+)', original_prompt.lower())
        priority_match = re.search(r'(high|low|medium|first|last|early)', original_prompt.lower())
        
        if node_match:
            node = int(node_match.group(1))
            priority = priority_match.group(1) if priority_match else "high"
            
            return ParsedConstraint(
                constraint_type="priority",
                subtype="service_priority",
                parameters={
                    "node": node,
                    "priority_level": priority,
                    "priority_type": "service_order"
                },
                entities=[
                    ConstraintEntity("node", str(node))
                ],
                mathematical_description=f"Priority constraint for node {node} with level {priority}",
                confidence=0.75,
                interpretation=f"Node {node} has {priority} priority for service",
                parsing_method="pattern_matching",
                complexity_level="simple",
                requires_preprocessing=True
            )
        
        return None

    def _parse_multi_part_constraint(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse multi-part constraints"""
        # This is complex - extract multiple constraint components
        min_vehicles = int(match.group(1))
        
        # Extract nodes directly from the regex match groups
        # The regex patterns capture the node numbers in groups 2 and 3
        try:
            node1 = int(match.group(2))
            node2 = int(match.group(3))
            nodes = [node1, node2]
        except (IndexError, ValueError):
            # Fallback: use findall if regex groups don't work
            node_matches = re.findall(r'node\s+(\d+)', original_prompt.lower())
            # For multi-part constraints, we want the nodes mentioned AFTER the vehicle count
            # Skip any nodes mentioned in the vehicle count part
            vehicle_part = original_prompt.lower().split('also')[0] if 'also' in original_prompt.lower() else original_prompt.lower().split('and')[0]
            node_part = original_prompt.lower().replace(vehicle_part, '')
            node_matches_in_constraint = re.findall(r'node\s+(\d+)', node_part)
            nodes = [int(n) for n in node_matches_in_constraint]
        
        # Determine the type of node constraint
        if "not be served together" in original_prompt.lower() or "different routes" in original_prompt.lower() or "be on different" in original_prompt.lower():
            constraint_subtype = "vehicle_count_and_separation"
            node_constraint_type = "separation"
        elif ("served together" in original_prompt.lower() or 
              "same route" in original_prompt.lower() or 
              "in same route" in original_prompt.lower() or 
              "on same route" in original_prompt.lower() or
              "be in same" in original_prompt.lower() or
              "be on same" in original_prompt.lower() or
              "together in a route" in original_prompt.lower() or
              "together in route" in original_prompt.lower() or
              "be together in" in original_prompt.lower() or
              "grouped in" in original_prompt.lower() or
              "grouped on" in original_prompt.lower() or
              "covered under same route" in original_prompt.lower() or
              "covered under the same route" in original_prompt.lower() or
              "handled under same route" in original_prompt.lower() or
              "managed under same route" in original_prompt.lower() or
              "covered by same route" in original_prompt.lower()):
            constraint_subtype = "vehicle_count_and_grouping"
            node_constraint_type = "grouping"
        else:
            constraint_subtype = "vehicle_count_and_custom"
            node_constraint_type = "custom"
        
        return ParsedConstraint(
            constraint_type="multi_part",
            subtype=constraint_subtype,
            parameters={
                "min_vehicles": min_vehicles,
                "nodes": nodes,
                "node_constraint_type": node_constraint_type
            },
            entities=[
                ConstraintEntity("vehicle", "all"),
                *[ConstraintEntity("node", str(n)) for n in nodes]
            ],
            mathematical_description=f"sum(used_k for all k) >= {min_vehicles} AND node constraint for nodes {nodes}",
            confidence=0.85,
            interpretation=f"Use at least {min_vehicles} vehicles and apply {node_constraint_type} constraint to nodes {nodes}",
            parsing_method="pattern_matching",
            complexity_level="complex",
            requires_preprocessing=True
        )

    def _llm_parse_constraint(self, prompt: str, context: Dict = None) -> Optional[ParsedConstraint]:
        """Use LLM for complex constraint parsing"""
        try:
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
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()
            
            # Extract JSON
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]
                
            result_dict = json.loads(content)
            
            # Convert to ParsedConstraint object
            entities = []
            for entity_type, entity_list in result_dict.get('entities', {}).items():
                for entity_id in entity_list:
                    entities.append(ConstraintEntity(entity_type.rstrip('s'), str(entity_id)))
            
            return ParsedConstraint(
                constraint_type=result_dict.get('constraint_type', 'custom'),
                subtype=result_dict.get('subtype'),
                parameters=result_dict.get('parameters', {}),
                entities=entities,
                mathematical_description=result_dict.get('mathematical_description', ''),
                confidence=result_dict.get('confidence', 0.8),
                interpretation=result_dict.get('interpretation', ''),
                parsing_method="llm",
                complexity_level=result_dict.get('complexity_level', 'medium'),
                requires_preprocessing=result_dict.get('requires_preprocessing', False)
            )

        except Exception as e:
            print(f"[Enhanced Parser] LLM parsing failed: {e}")
            return None

    def _fallback_parse_constraint(self, prompt: str) -> ParsedConstraint:
        """Fallback parsing for unrecognized constraints"""
        return ParsedConstraint(
            constraint_type="custom",
            subtype="unrecognized",
            parameters={"raw_constraint": prompt},
            entities=[],
            mathematical_description="Custom constraint requiring manual interpretation",
            confidence=0.3,
            interpretation=f"Could not automatically parse: '{prompt}'. Manual review required.",
            parsing_method="fallback",
            complexity_level="unknown",
            requires_preprocessing=True
        )

    def is_available(self) -> bool:
        """Check if enhanced parsing is available"""
        return True  # Pattern matching is always available, LLM is optional 