#!/usr/bin/env python3
"""
Enhanced Constraint Parser for Inventory Optimization
Handles natural language constraints with pattern matching and LLM fallback
"""

import re
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Try to import OpenAI
OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    print("[Inventory Parser] OpenAI not available, will use pattern matching only")

@dataclass
class ConstraintEntity:
    """Represents an entity in a constraint (item, category, supplier)"""
    type: str  # 'item', 'category', 'supplier', 'metric'
    id: str    # identifier
    properties: Dict = None

@dataclass
class ParsedConstraint:
    """Enhanced constraint representation for inventory"""
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

class EnhancedInventoryConstraintParser:
    """Enhanced parser for complex inventory constraints"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._get_api_key()
        self.client = None
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                print(f"[Inventory Parser] OpenAI client initialized successfully")
            except Exception as e:
                print(f"[Inventory Parser] Failed to initialize OpenAI client: {e}")
        
        self.system_prompt = self._create_enhanced_system_prompt()
        
        # Define constraint patterns for inventory optimization
        self.constraint_patterns = {
            'safety_stock': [
                r'(\w+)\s+safety\s*stock\s+(?:should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'item\s+(\w+)\s+(?:should\s+have\s+)?safety\s*stock\s+([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'minimum\s+safety\s*stock\s+(?:for\s+)?(\w+)\s+(?:should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'(\w+)\s+(?:must\s+have\s+)?(?:at\s+least|minimum)\s+(\d+(?:\.\d+)?)\s+(?:units?\s+)?safety\s*stock',
                r'keep\s+(\w+)\s+safety\s*stock\s+(?:above|below|at)\s+(\d+(?:\.\d+)?)'
            ],
            'eoq': [
                r'(\w+)\s+(?:EOQ|order\s*quantity)\s+(?:must\s+be\s+|should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'economic\s+order\s+quantity\s+(?:for\s+)?(\w+)\s+([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'(\w+)\s+(?:should\s+)?order\s+(?:at\s+least|at\s+most|exactly)\s+(\d+(?:\.\d+)?)\s+(?:units?)?',
                r'minimum\s+order\s+(?:size|quantity)\s+(?:for\s+)?(\w+)\s+(?:is\s+)?(\d+(?:\.\d+)?)',
                r'(\w+)\s+batch\s+size\s+([<>=]+)\s*(\d+(?:\.\d+)?)'
            ],
            'inventory_value': [
                r'(\w+)\s+inventory\s*value\s+(?:should\s+be\s+|must\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'total\s+(?:inventory\s+)?value\s+(?:for\s+)?(\w+)\s+([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'keep\s+(\w+)\s+(?:inventory\s+)?value\s+(?:below|under|above)\s+\$?(\d+(?:\.\d+)?)',
                r'(\w+)\s+(?:should\s+)?(?:not\s+)?exceed\s+\$?(\d+(?:\.\d+)?)\s+(?:in\s+)?inventory\s*value',
                r'maximum\s+inventory\s+investment\s+(?:for\s+)?(\w+)\s+(?:is\s+)?\$?(\d+(?:\.\d+)?)'
            ],
            'service_level': [
                r'(\w+)\s+service\s*level\s+(?:should\s+be\s+|must\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)\s*%?',
                r'maintain\s+(\d+(?:\.\d+)?)\s*%?\s+service\s*level\s+(?:for\s+)?(\w+)',
                r'(\w+)\s+(?:must\s+)?achieve\s+(?:at\s+least\s+)?(\d+(?:\.\d+)?)\s*%?\s+availability',
                r'target\s+fill\s*rate\s+(?:for\s+)?(\w+)\s+(?:is\s+)?(\d+(?:\.\d+)?)\s*%?'
            ],
            'reorder_point': [
                r'(\w+)\s+reorder\s*point\s+(?:should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'reorder\s+(\w+)\s+(?:when\s+inventory\s+)?(?:reaches|falls\s+to)\s+(\d+(?:\.\d+)?)',
                r'(\w+)\s+(?:should\s+)?(?:be\s+)?reordered\s+(?:at|when)\s+(\d+(?:\.\d+)?)\s+units?'
            ],
            'category_constraints': [
                r'(?:all\s+)?category\s+(\w+)\s+items?\s+(?:should\s+have\s+)?(\w+)\s+([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'(\w+)\s+items?\s+(?:in\s+)?category\s+(\w+)',
                r'apply\s+(\w+)\s+(?:constraint|limit)\s+(?:to\s+)?category\s+(\w+)',
                r'for\s+(?:all\s+)?(\w+)\s+category\s+items?,?\s+(.+)'
            ],
            'supplier_constraints': [
                r'supplier\s+(\w+)\s+items?\s+(?:should\s+have\s+)?(\w+)\s+([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'(?:all\s+)?items?\s+from\s+supplier\s+(\w+)\s+(.+)',
                r'(\w+)\s+supplier\s+(?:must\s+|should\s+)?(.+)'
            ],
            'multi_item': [
                r'items?\s+(\w+)\s+(?:and|,)\s+(\w+)\s+(?:and|,)?\s*(\w+)?\s+(?:should|must)\s+(.+)',
                r'for\s+items?\s+(\w+)(?:\s*,\s*(\w+))*\s*(?:and\s+)?(\w+)?,?\s+(.+)',
                r'(\w+),?\s+(\w+)(?:,?\s+and\s+)?(\w+)?\s+(?:should\s+)?have\s+(.+)'
            ],
            'holding_cost': [
                r'(\w+)\s+holding\s*cost\s+(?:should\s+be\s+)?([<>=]+)\s*(\d+(?:\.\d+)?)',
                r'minimize\s+holding\s*cost\s+(?:for\s+)?(\w+)',
                r'reduce\s+storage\s*cost\s+(?:for\s+)?(\w+)\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*%?'
            ],
            'complex_rules': [
                r'(?:if|when)\s+(.+?)\s+(?:then|,)\s+(.+)',
                r'(.+?)\s+(?:only\s+)?if\s+(.+)',
                r'(?:ensure|make\s+sure)\s+(.+?)\s+(?:while|but)\s+(.+)'
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
You are an advanced constraint parser for Inventory Optimization Problems. You can handle complex inventory constraints including:

1. Safety stock constraints (minimum/maximum safety stock levels)
2. Economic Order Quantity (EOQ) constraints (order size limits)
3. Inventory value constraints (budget limits per item or total)
4. Service level constraints (availability, fill rate targets)
5. Reorder point constraints (when to trigger orders)
6. Category-based constraints (rules for groups of items)
7. Supplier-based constraints (rules for items from specific suppliers)
8. Multi-item constraints (rules affecting multiple specific items)
9. Holding cost constraints (storage cost limits)
10. Complex conditional rules (if-then scenarios)

For each constraint, extract:
- constraint_type: [safety_stock, eoq, inventory_value, service_level, reorder_point, category_constraint, supplier_constraint, multi_item, holding_cost, complex_rule, custom]
- subtype: More specific classification
- parameters: All relevant parameters including operators, values, conditions
- entities: Involved items, categories, suppliers
- mathematical_description: Mathematical formulation if applicable
- complexity_level: [simple, medium, complex]

Output JSON format:
{
    "constraint_type": "string",
    "subtype": "string", 
    "parameters": {
        "key": "value"
    },
    "entities": {
        "items": ["list of item IDs"],
        "categories": ["list of categories"],
        "suppliers": ["list of suppliers"],
        "metrics": ["list of metrics affected"]
    },
    "mathematical_description": "mathematical formulation",
    "confidence": 0.95,
    "interpretation": "human-readable interpretation",
    "complexity_level": "simple|medium|complex",
    "requires_preprocessing": false
}

Examples:

Input: "ITEM001 safety stock should be <= 10"
Output: {
    "constraint_type": "safety_stock",
    "subtype": "upper_limit",
    "parameters": {
        "item_id": "ITEM001",
        "operator": "<=",
        "value": 10,
        "units": "units"
    },
    "entities": {
        "items": ["ITEM001"],
        "categories": [],
        "suppliers": [],
        "metrics": ["safety_stock"]
    },
    "mathematical_description": "safety_stock[ITEM001] <= 10",
    "confidence": 0.95,
    "interpretation": "Safety stock for ITEM001 must not exceed 10 units",
    "complexity_level": "simple",
    "requires_preprocessing": false
}

Input: "All category A items should have EOQ >= 50"
Output: {
    "constraint_type": "category_constraint",
    "subtype": "eoq_by_category",
    "parameters": {
        "category": "A",
        "metric": "eoq",
        "operator": ">=",
        "value": 50
    },
    "entities": {
        "items": ["all_in_category_A"],
        "categories": ["A"],
        "suppliers": [],
        "metrics": ["eoq"]
    },
    "mathematical_description": "EOQ[i] >= 50 for all i in category A",
    "confidence": 0.90,
    "interpretation": "All items in category A must have an EOQ of at least 50 units",
    "complexity_level": "medium",
    "requires_preprocessing": true
}

Input: "Keep safety stock for high-value items above 15 units"
Output: {
    "constraint_type": "complex_rule",
    "subtype": "conditional_safety_stock",
    "parameters": {
        "condition": "high_value_items",
        "metric": "safety_stock",
        "operator": ">",
        "value": 15,
        "value_threshold": "needs_definition"
    },
    "entities": {
        "items": ["high_value_items"],
        "categories": [],
        "suppliers": [],
        "metrics": ["safety_stock", "unit_cost"]
    },
    "mathematical_description": "safety_stock[i] > 15 for all i where unit_cost[i] > threshold",
    "confidence": 0.85,
    "interpretation": "Items classified as high-value must maintain safety stock above 15 units",
    "complexity_level": "complex",
    "requires_preprocessing": true
}

Handle typos, informal language, and ambiguous cases gracefully. Consider business context and standard inventory management practices.
"""

    def parse_constraint(self, prompt: str, context: Dict = None) -> ParsedConstraint:
        """Parse constraint using enhanced pattern matching and LLM"""
        print(f"[Inventory Parser] Parsing constraint: '{prompt}'")
        
        # First try pattern matching for known constraint types
        pattern_result = self._pattern_match_constraint(prompt)
        if pattern_result and pattern_result.confidence > 0.8:
            print(f"[Inventory Parser] High confidence pattern match: {pattern_result.constraint_type}")
            return pattern_result
        
        # If pattern matching fails or has low confidence, use LLM
        if self.client:
            llm_result = self._llm_parse_constraint(prompt, context)
            if llm_result:
                print(f"[Inventory Parser] LLM parsing successful: {llm_result.constraint_type}")
                return llm_result
        
        # Fallback to basic parsing
        print(f"[Inventory Parser] Using fallback parsing")
        return self._fallback_parse_constraint(prompt)

    def _pattern_match_constraint(self, prompt: str) -> Optional[ParsedConstraint]:
        """Pattern matching for inventory constraints"""
        prompt_lower = prompt.lower().strip()
        
        # Check each constraint type
        constraint_types = [
            ('safety_stock', self._parse_safety_stock),
            ('eoq', self._parse_eoq),
            ('inventory_value', self._parse_inventory_value),
            ('service_level', self._parse_service_level),
            ('reorder_point', self._parse_reorder_point),
            ('category_constraints', self._parse_category_constraint),
            ('supplier_constraints', self._parse_supplier_constraint),
            ('multi_item', self._parse_multi_item),
            ('holding_cost', self._parse_holding_cost),
            ('complex_rules', self._parse_complex_rule)
        ]
        
        for constraint_type, parser_func in constraint_types:
            patterns = self.constraint_patterns.get(constraint_type, [])
            for pattern in patterns:
                match = re.search(pattern, prompt_lower, re.IGNORECASE)
                if match:
                    result = parser_func(match, prompt)
                    if result:
                        return result
        
        return None

    def _parse_safety_stock(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse safety stock constraints"""
        groups = match.groups()
        
        # Handle different pattern formats
        if len(groups) >= 3 and groups[0] and groups[1] and groups[2]:
            item_id = groups[0].upper()
            operator = groups[1]
            value = float(groups[2])
        elif len(groups) >= 2:
            # Pattern like "ITEM001 must have at least 10 units safety stock"
            item_id = groups[0].upper()
            value = float(groups[1])
            if 'at least' in original_prompt.lower():
                operator = '>='
            elif 'at most' in original_prompt.lower():
                operator = '<='
            else:
                operator = '='
        else:
            return None
        
        return ParsedConstraint(
            constraint_type="safety_stock",
            subtype="item_specific",
            parameters={
                "item_id": item_id,
                "operator": operator,
                "value": value,
                "units": "units"
            },
            entities=[
                ConstraintEntity("item", item_id),
                ConstraintEntity("metric", "safety_stock")
            ],
            mathematical_description=f"safety_stock[{item_id}] {operator} {value}",
            confidence=0.90,
            interpretation=f"Safety stock for {item_id} must be {operator} {value} units",
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_eoq(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse EOQ constraints"""
        groups = match.groups()
        
        if len(groups) >= 3:
            item_id = groups[0].upper()
            operator = groups[1]
            value = float(groups[2])
        elif len(groups) >= 2:
            item_id = groups[0].upper()
            value = float(groups[1])
            if 'at least' in original_prompt.lower() or 'minimum' in original_prompt.lower():
                operator = '>='
            elif 'at most' in original_prompt.lower() or 'maximum' in original_prompt.lower():
                operator = '<='
            else:
                operator = '='
        else:
            return None
        
        return ParsedConstraint(
            constraint_type="eoq",
            subtype="order_quantity_limit",
            parameters={
                "item_id": item_id,
                "operator": operator,
                "value": value,
                "units": "units"
            },
            entities=[
                ConstraintEntity("item", item_id),
                ConstraintEntity("metric", "eoq")
            ],
            mathematical_description=f"EOQ[{item_id}] {operator} {value}",
            confidence=0.90,
            interpretation=f"Economic Order Quantity for {item_id} must be {operator} {value} units",
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_inventory_value(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse inventory value constraints"""
        groups = match.groups()
        
        # Extract item and value
        if len(groups) >= 3:
            item_id = groups[0].upper()
            operator = groups[1]
            value = float(groups[2])
        elif len(groups) >= 2:
            item_id = groups[0].upper()
            value = float(groups[1])
            if 'below' in original_prompt.lower() or 'under' in original_prompt.lower():
                operator = '<'
            elif 'above' in original_prompt.lower():
                operator = '>'
            elif 'exceed' in original_prompt.lower():
                operator = '<=' if 'not' in original_prompt.lower() else '>'
            else:
                operator = '<='
        else:
            return None
        
        return ParsedConstraint(
            constraint_type="inventory_value",
            subtype="value_limit",
            parameters={
                "item_id": item_id,
                "operator": operator,
                "value": value,
                "currency": "USD"
            },
            entities=[
                ConstraintEntity("item", item_id),
                ConstraintEntity("metric", "inventory_value")
            ],
            mathematical_description=f"inventory_value[{item_id}] {operator} {value}",
            confidence=0.85,
            interpretation=f"Inventory value for {item_id} must be {operator} ${value}",
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_service_level(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse service level constraints"""
        groups = match.groups()
        
        # Handle different pattern formats
        if groups[0] and groups[0].replace('.', '').isdigit():
            # Pattern like "maintain 95% service level for ITEM001"
            value = float(groups[0])
            item_id = groups[1].upper() if len(groups) > 1 and groups[1] else "ALL"
        else:
            # Pattern like "ITEM001 service level >= 95%"
            item_id = groups[0].upper()
            if len(groups) >= 3:
                operator = groups[1]
                value = float(groups[2])
            else:
                value = float(groups[1]) if len(groups) > 1 else 95.0
                operator = '>='
        
        # Normalize percentage
        if value > 1:
            value = value / 100
        
        return ParsedConstraint(
            constraint_type="service_level",
            subtype="availability_target",
            parameters={
                "item_id": item_id,
                "operator": operator if 'operator' in locals() else '>=',
                "value": value,
                "as_percentage": value * 100
            },
            entities=[
                ConstraintEntity("item", item_id),
                ConstraintEntity("metric", "service_level")
            ],
            mathematical_description=f"service_level[{item_id}] >= {value}",
            confidence=0.85,
            interpretation=f"Service level for {item_id} must be at least {value*100}%",
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_reorder_point(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse reorder point constraints"""
        groups = match.groups()
        
        item_id = groups[0].upper()
        if len(groups) >= 3:
            operator = groups[1]
            value = float(groups[2])
        else:
            value = float(groups[1])
            operator = '='
        
        return ParsedConstraint(
            constraint_type="reorder_point",
            subtype="reorder_trigger",
            parameters={
                "item_id": item_id,
                "operator": operator,
                "value": value,
                "units": "units"
            },
            entities=[
                ConstraintEntity("item", item_id),
                ConstraintEntity("metric", "reorder_point")
            ],
            mathematical_description=f"reorder_point[{item_id}] {operator} {value}",
            confidence=0.85,
            interpretation=f"Reorder point for {item_id} must be {operator} {value} units",
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_category_constraint(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse category-based constraints"""
        groups = match.groups()
        
        # Extract category and constraint details
        category = None
        metric = None
        operator = None
        value = None
        
        # Find category
        for g in groups:
            if g and g.upper() in ['A', 'B', 'C'] or g.lower() in ['high', 'medium', 'low', 'critical']:
                category = g.upper()
                break
        
        # Extract metric and value from the prompt
        metrics = ['safety stock', 'eoq', 'inventory value', 'service level', 'holding cost']
        for m in metrics:
            if m in original_prompt.lower():
                metric = m.replace(' ', '_')
                break
        
        # Extract operator and value
        op_value_match = re.search(r'([<>=]+)\s*(\d+(?:\.\d+)?)', original_prompt)
        if op_value_match:
            operator = op_value_match.group(1)
            value = float(op_value_match.group(2))
        
        if not all([category, metric, value]):
            return None
        
        return ParsedConstraint(
            constraint_type="category_constraint",
            subtype=f"{metric}_by_category",
            parameters={
                "category": category,
                "metric": metric,
                "operator": operator or '>=',
                "value": value
            },
            entities=[
                ConstraintEntity("category", category),
                ConstraintEntity("metric", metric)
            ],
            mathematical_description=f"{metric}[i] {operator or '>='} {value} for all i in category {category}",
            confidence=0.80,
            interpretation=f"All items in category {category} must have {metric} {operator or '>='} {value}",
            parsing_method="pattern_matching",
            complexity_level="medium",
            requires_preprocessing=True
        )

    def _parse_supplier_constraint(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse supplier-based constraints"""
        groups = match.groups()
        
        # Extract supplier
        supplier = None
        for g in groups:
            if g and 'SUP' in g.upper():
                supplier = g.upper()
                break
        
        if not supplier:
            # Try to find any word that could be a supplier name
            supplier_match = re.search(r'supplier\s+(\w+)', original_prompt, re.IGNORECASE)
            if supplier_match:
                supplier = supplier_match.group(1).upper()
        
        # Extract constraint details similar to category constraints
        metric = None
        metrics = ['safety stock', 'eoq', 'inventory value', 'lead time']
        for m in metrics:
            if m in original_prompt.lower():
                metric = m.replace(' ', '_')
                break
        
        # Extract operator and value
        op_value_match = re.search(r'([<>=]+)\s*(\d+(?:\.\d+)?)', original_prompt)
        if op_value_match:
            operator = op_value_match.group(1)
            value = float(op_value_match.group(2))
        else:
            operator = '>='
            value = 0
        
        if not supplier:
            return None
        
        return ParsedConstraint(
            constraint_type="supplier_constraint",
            subtype=f"{metric or 'general'}_by_supplier",
            parameters={
                "supplier": supplier,
                "metric": metric,
                "operator": operator,
                "value": value
            },
            entities=[
                ConstraintEntity("supplier", supplier),
                ConstraintEntity("metric", metric or "general")
            ],
            mathematical_description=f"{metric}[i] {operator} {value} for all i from supplier {supplier}",
            confidence=0.75,
            interpretation=f"All items from supplier {supplier} must have {metric} {operator} {value}",
            parsing_method="pattern_matching",
            complexity_level="medium",
            requires_preprocessing=True
        )

    def _parse_multi_item(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse multi-item constraints"""
        groups = match.groups()
        
        # Extract item IDs
        items = []
        for g in groups[:3]:  # First 3 groups should be item IDs
            if g and g.strip():
                items.append(g.upper())
        
        # Extract constraint from the last group
        constraint_text = groups[-1] if len(groups) > 0 else ""
        
        # Determine constraint type from text
        metric = None
        operator = '='
        value = None
        
        if 'same' in constraint_text.lower():
            constraint_type = "uniformity"
            interpretation = f"Items {', '.join(items)} should have the same values"
        else:
            # Try to extract metric and value
            for m in ['safety stock', 'eoq', 'service level']:
                if m in constraint_text.lower():
                    metric = m.replace(' ', '_')
                    break
            
            op_value_match = re.search(r'([<>=]+)\s*(\d+(?:\.\d+)?)', constraint_text)
            if op_value_match:
                operator = op_value_match.group(1)
                value = float(op_value_match.group(2))
            
            constraint_type = "multi_item_limit"
            interpretation = f"Items {', '.join(items)} must have {metric or 'value'} {operator} {value}"
        
        return ParsedConstraint(
            constraint_type="multi_item",
            subtype=constraint_type,
            parameters={
                "items": items,
                "metric": metric,
                "operator": operator,
                "value": value,
                "constraint_text": constraint_text
            },
            entities=[
                *[ConstraintEntity("item", item) for item in items],
                ConstraintEntity("metric", metric or "general")
            ],
            mathematical_description=f"{metric or 'metric'}[i] {operator} {value} for i in {items}",
            confidence=0.70,
            interpretation=interpretation,
            parsing_method="pattern_matching",
            complexity_level="medium",
            requires_preprocessing=True
        )

    def _parse_holding_cost(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse holding cost constraints"""
        groups = match.groups()
        
        item_id = groups[0].upper() if groups[0] else "ALL"
        
        if 'minimize' in original_prompt.lower() or 'reduce' in original_prompt.lower():
            subtype = "minimize"
            interpretation = f"Minimize holding cost for {item_id}"
            math_desc = f"minimize holding_cost[{item_id}]"
        else:
            operator = groups[1] if len(groups) > 1 else '<='
            value = float(groups[2]) if len(groups) > 2 else 0
            subtype = "limit"
            interpretation = f"Holding cost for {item_id} must be {operator} ${value}"
            math_desc = f"holding_cost[{item_id}] {operator} {value}"
        
        return ParsedConstraint(
            constraint_type="holding_cost",
            subtype=subtype,
            parameters={
                "item_id": item_id,
                "operator": operator if subtype == "limit" else None,
                "value": value if subtype == "limit" else None
            },
            entities=[
                ConstraintEntity("item", item_id),
                ConstraintEntity("metric", "holding_cost")
            ],
            mathematical_description=math_desc,
            confidence=0.80,
            interpretation=interpretation,
            parsing_method="pattern_matching",
            complexity_level="simple",
            requires_preprocessing=False
        )

    def _parse_complex_rule(self, match, original_prompt: str) -> ParsedConstraint:
        """Parse complex conditional rules"""
        groups = match.groups()
        
        condition = groups[0] if groups[0] else ""
        action = groups[1] if len(groups) > 1 else ""
        
        return ParsedConstraint(
            constraint_type="complex_rule",
            subtype="conditional",
            parameters={
                "condition": condition,
                "action": action,
                "full_rule": original_prompt
            },
            entities=[],
            mathematical_description="Complex conditional constraint",
            confidence=0.60,
            interpretation=f"If {condition}, then {action}",
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
                    {"role": "user", "content": f"Parse this inventory constraint: '{prompt}'{context_info}"}
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
            print(f"[Inventory Parser] LLM parsing failed: {e}")
            return None

    def _fallback_parse_constraint(self, prompt: str) -> ParsedConstraint:
        """Improved fallback parsing for unrecognized constraints"""
        # Try to extract basic patterns even if they don't match exactly
        prompt_lower = prompt.lower()
        
        # Look for item IDs
        item_matches = re.findall(r'\b(ITEM\d+|[A-Z]+\d+)\b', prompt, re.IGNORECASE)
        items = [m.upper() for m in item_matches]
        
        # Look for numeric values
        value_matches = re.findall(r'\b(\d+(?:\.\d+)?)\b', prompt)
        values = [float(v) for v in value_matches]
        
        # Look for operators
        operators = []
        for op in ['<=', '>=', '<', '>', '=', '==']:
            if op in prompt:
                operators.append(op)
        
        # Look for keywords to determine constraint type
        constraint_type = "custom"
        if 'safety stock' in prompt_lower:
            constraint_type = "safety_stock"
        elif 'eoq' in prompt_lower or 'order quantity' in prompt_lower:
            constraint_type = "eoq"
        elif 'inventory value' in prompt_lower or 'value' in prompt_lower:
            constraint_type = "inventory_value"
        elif 'service level' in prompt_lower or 'availability' in prompt_lower:
            constraint_type = "service_level"
        elif 'reorder' in prompt_lower:
            constraint_type = "reorder_point"
        
        return ParsedConstraint(
            constraint_type=constraint_type,
            subtype="fallback_parsed",
            parameters={
                "raw_constraint": prompt,
                "extracted_items": items,
                "extracted_values": values,
                "extracted_operators": operators
            },
            entities=[ConstraintEntity("item", item) for item in items],
            mathematical_description="Unable to parse precise mathematical formulation",
            confidence=0.3,
            interpretation=f"Constraint: {prompt} (requires manual review)",
            parsing_method="fallback",
            complexity_level="unknown",
            requires_preprocessing=True
        )

    def is_available(self) -> bool:
        """Check if parser is fully available (with LLM support)"""
        return self.client is not None 