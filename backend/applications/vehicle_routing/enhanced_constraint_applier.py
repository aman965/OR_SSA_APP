#!/usr/bin/env python3
"""
Enhanced Constraint Applier for Complex VRP Constraints
Applies advanced routing constraints to the PuLP optimization model
"""

from typing import Dict, List, Any
from pulp import lpSum, LpVariable

# Import with absolute path to avoid relative import issues
try:
    from enhanced_constraint_parser import ParsedConstraint, ConstraintEntity
except ImportError:
    # Fallback for when running as a module
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from enhanced_constraint_parser import ParsedConstraint, ConstraintEntity


class EnhancedConstraintApplier:
    """Applies complex constraints to VRP optimization models"""
    
    def __init__(self, problem_context: Dict = None):
        self.problem_context = problem_context or {}
        self.applied_constraints = []
        self.constraint_counters = {}
        
    def apply_constraints_to_model(self, prob, constraints: List[ParsedConstraint], 
                                 nodes, vehicle_count, vehicle_capacity, demand, 
                                 used_k, x, u) -> Dict:
        """
        Apply a list of parsed constraints to the PuLP model
        
        Args:
            prob: PuLP problem instance
            constraints: List of ParsedConstraint objects
            nodes: List of node indices
            vehicle_count: Number of available vehicles
            vehicle_capacity: Vehicle capacity
            demand: List of node demands
            used_k: Binary variables for vehicle usage
            x: Binary variables for route decisions
            u: Continuous variables for MTZ constraints
            
        Returns:
            Dict with application results and statistics
        """
        application_results = {
            "total_constraints": len(constraints),
            "applied_successfully": 0,
            "failed_applications": 0,
            "warnings": [],
            "constraint_details": []
        }
        
        for i, constraint in enumerate(constraints):
            try:
                result = self._apply_single_constraint(
                    prob, constraint, nodes, vehicle_count, vehicle_capacity, 
                    demand, used_k, x, u, i
                )
                
                if result["success"]:
                    application_results["applied_successfully"] += 1
                    self.applied_constraints.append(constraint)
                else:
                    application_results["failed_applications"] += 1
                    application_results["warnings"].append(
                        f"Failed to apply constraint {i+1}: {result['error']}"
                    )
                
                application_results["constraint_details"].append(result)
                
            except Exception as e:
                application_results["failed_applications"] += 1
                application_results["warnings"].append(
                    f"Error applying constraint {i+1}: {str(e)}"
                )
                print(f"[Enhanced Applier] Error applying constraint {i+1}: {e}")
        
        return application_results
    
    def _apply_single_constraint(self, prob, constraint: ParsedConstraint, 
                               nodes, vehicle_count, vehicle_capacity, demand, 
                               used_k, x, u, constraint_index: int) -> Dict:
        """Apply a single constraint to the model"""
        
        constraint_type = constraint.constraint_type
        constraint_id = f"{constraint_type}_{constraint_index}"
        
        print(f"[Enhanced Applier] Applying {constraint_type} constraint: {constraint.interpretation}")
        
        try:
            if constraint_type == "node_separation":
                return self._apply_node_separation(prob, constraint, nodes, vehicle_count, x, constraint_id)
            
            elif constraint_type == "node_grouping":
                return self._apply_node_grouping(prob, constraint, nodes, vehicle_count, x, constraint_id)
            
            elif constraint_type == "vehicle_assignment":
                return self._apply_vehicle_assignment(prob, constraint, nodes, x, constraint_id)
            
            elif constraint_type == "route_constraint":
                return self._apply_route_constraint(prob, constraint, nodes, vehicle_count, x, constraint_id)
            
            elif constraint_type == "vehicle_count":
                return self._apply_vehicle_count_constraint(prob, constraint, vehicle_count, used_k, constraint_id)
            
            elif constraint_type == "multi_part":
                return self._apply_multi_part_constraint(
                    prob, constraint, nodes, vehicle_count, vehicle_capacity, 
                    demand, used_k, x, u, constraint_id
                )
            
            elif constraint_type == "priority":
                return self._apply_priority_constraint(prob, constraint, nodes, vehicle_count, x, constraint_id)
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown constraint type: {constraint_type}",
                    "constraint_type": constraint_type,
                    "mathematical_constraints_added": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception during application: {str(e)}",
                "constraint_type": constraint_type,
                "mathematical_constraints_added": 0
            }
    
    def _apply_node_separation(self, prob, constraint: ParsedConstraint, nodes, 
                             vehicle_count, x, constraint_id: str) -> Dict:
        """Apply node separation constraints (nodes cannot be on same route)"""
        
        params = constraint.parameters
        node1 = int(params["node_1"])
        node2 = int(params["node_2"])
        
        # Validate nodes exist
        if node1 not in nodes or node2 not in nodes:
            return {
                "success": False,
                "error": f"Invalid nodes: {node1}, {node2} not in node set {nodes}",
                "constraint_type": "node_separation",
                "mathematical_constraints_added": 0
            }
        
        constraints_added = 0
        
        # For each vehicle, ensure that if one node is served by the vehicle,
        # the other node is not served by the same vehicle
        for k in range(vehicle_count):
            # If node1 is visited by vehicle k, then node2 cannot be visited by vehicle k
            prob += (
                lpSum(x[i, node1, k] for i in nodes if i != node1) + 
                lpSum(x[i, node2, k] for i in nodes if i != node2)
            ) <= 1, f"NodeSeparation_{node1}_{node2}_Vehicle_{k}_{constraint_id}"
            constraints_added += 1
        
        print(f"[Enhanced Applier] Applied node separation: nodes {node1} and {node2} cannot be on same route")
        
        return {
            "success": True,
            "constraint_type": "node_separation",
            "mathematical_constraints_added": constraints_added,
            "details": f"Nodes {node1} and {node2} separated across {vehicle_count} vehicles"
        }
    
    def _apply_node_grouping(self, prob, constraint: ParsedConstraint, nodes, 
                           vehicle_count, x, constraint_id: str) -> Dict:
        """Apply node grouping constraints (nodes must be on same route)"""
        
        params = constraint.parameters
        node1 = int(params["node_1"])
        node2 = int(params["node_2"])
        
        # Validate nodes exist
        if node1 not in nodes or node2 not in nodes:
            return {
                "success": False,
                "error": f"Invalid nodes: {node1}, {node2} not in node set {nodes}",
                "constraint_type": "node_grouping",
                "mathematical_constraints_added": 0
            }
        
        constraints_added = 0
        
        # Method 1: For each vehicle k, ensure that both nodes have the same "visited" status
        for k in range(vehicle_count):
            # Both nodes must have the same incoming edge count for vehicle k
            prob += (
                lpSum(x[i, node1, k] for i in nodes if i != node1) == 
                lpSum(x[i, node2, k] for i in nodes if i != node2)
            ), f"NodeGrouping_Same_{node1}_{node2}_Vehicle_{k}_{constraint_id}"
            constraints_added += 1
        
        # Method 2: Cross-vehicle exclusion - if any vehicle visits one node, no other vehicle can visit the other
        for k in range(vehicle_count):
            for other_k in range(vehicle_count):
                if k != other_k:
                    # If node1 is visited by vehicle k, then node2 cannot be visited by vehicle other_k
                    prob += (
                        lpSum(x[i, node1, k] for i in nodes if i != node1) + 
                        lpSum(x[i, node2, other_k] for i in nodes if i != node2)
                    ) <= 1, f"NodeGrouping_Exclusive_{node1}_{node2}_V{k}_V{other_k}_{constraint_id}"
                    constraints_added += 1
        
        # Method 3: Strong coupling constraint - if either node is visited, both must be visited by the same vehicle
        # This creates a binary variable for each vehicle indicating if both nodes are served by that vehicle
        from pulp import LpVariable, LpBinary
        
        # Create auxiliary variables for each vehicle indicating if both nodes are served together
        both_served_vars = {}
        for k in range(vehicle_count):
            both_served_vars[k] = LpVariable(f"BothServed_{node1}_{node2}_V{k}_{constraint_id}", cat=LpBinary)
            
            # If both_served[k] = 1, then both nodes must be served by vehicle k
            prob += (
                lpSum(x[i, node1, k] for i in nodes if i != node1) >= both_served_vars[k]
            ), f"NodeGrouping_Force1_{node1}_{node2}_V{k}_{constraint_id}"
            constraints_added += 1
            
            prob += (
                lpSum(x[i, node2, k] for i in nodes if i != node2) >= both_served_vars[k]
            ), f"NodeGrouping_Force2_{node1}_{node2}_V{k}_{constraint_id}"
            constraints_added += 1
            
            # If either node is served by vehicle k, then both_served[k] must be 1
            prob += (
                both_served_vars[k] >= lpSum(x[i, node1, k] for i in nodes if i != node1)
            ), f"NodeGrouping_Trigger1_{node1}_{node2}_V{k}_{constraint_id}"
            constraints_added += 1
            
            prob += (
                both_served_vars[k] >= lpSum(x[i, node2, k] for i in nodes if i != node2)
            ), f"NodeGrouping_Trigger2_{node1}_{node2}_V{k}_{constraint_id}"
            constraints_added += 1
        
        # Ensure exactly one vehicle serves both nodes (if they are served at all)
        prob += (
            lpSum(both_served_vars[k] for k in range(vehicle_count)) <= 1
        ), f"NodeGrouping_OnlyOne_{node1}_{node2}_{constraint_id}"
        constraints_added += 1
        
        print(f"[Enhanced Applier] Applied STRONG node grouping: nodes {node1} and {node2} must be on same route")
        print(f"[Enhanced Applier] Added {constraints_added} mathematical constraints for strong grouping")
        
        return {
            "success": True,
            "constraint_type": "node_grouping",
            "mathematical_constraints_added": constraints_added,
            "details": f"Nodes {node1} and {node2} grouped with STRONG constraints ({constraints_added} total)"
        }
    
    def _apply_vehicle_assignment(self, prob, constraint: ParsedConstraint, nodes, 
                                x, constraint_id: str) -> Dict:
        """Apply vehicle assignment constraints (specific node to specific vehicle)"""
        
        params = constraint.parameters
        node = int(params["node"])
        vehicle = int(params["vehicle"])
        
        # Validate node exists
        if node not in nodes:
            return {
                "success": False,
                "error": f"Invalid node: {node} not in node set {nodes}",
                "constraint_type": "vehicle_assignment",
                "mathematical_constraints_added": 0
            }
        
        constraints_added = 0
        
        # Node must be served by the specified vehicle
        prob += (
            lpSum(x[i, node, vehicle] for i in nodes if i != node) == 1
        ), f"VehicleAssignment_Node_{node}_Vehicle_{vehicle}_{constraint_id}"
        constraints_added += 1
        
        # Node cannot be served by any other vehicle
        for k in range(len(nodes)):  # Assuming vehicle_count is related to nodes
            if k != vehicle:
                prob += (
                    lpSum(x[i, node, k] for i in nodes if i != node) == 0
                ), f"VehicleAssignment_Node_{node}_NotVehicle_{k}_{constraint_id}"
                constraints_added += 1
        
        print(f"[Enhanced Applier] Applied vehicle assignment: node {node} assigned to vehicle {vehicle}")
        
        return {
            "success": True,
            "constraint_type": "vehicle_assignment",
            "mathematical_constraints_added": constraints_added,
            "details": f"Node {node} assigned to vehicle {vehicle}"
        }
    
    def _apply_route_constraint(self, prob, constraint: ParsedConstraint, nodes, 
                              vehicle_count, x, constraint_id: str) -> Dict:
        """Apply route-level constraints (distance, time limits)"""
        
        params = constraint.parameters
        max_distance = float(params.get("max_distance", float('inf')))
        
        # This is a simplified implementation - in practice, you'd need distance matrix
        constraints_added = 0
        
        # For now, we'll add a placeholder constraint
        # In a real implementation, you'd use the actual distance matrix
        print(f"[Enhanced Applier] Route constraint noted: max distance {max_distance}")
        print(f"[Enhanced Applier] Note: Route distance constraints require distance matrix integration")
        
        return {
            "success": True,
            "constraint_type": "route_constraint",
            "mathematical_constraints_added": constraints_added,
            "details": f"Route constraint noted (requires distance matrix): max distance {max_distance}",
            "warning": "Route constraints require distance matrix integration for full implementation"
        }
    
    def _apply_vehicle_count_constraint(self, prob, constraint: ParsedConstraint, 
                                      vehicle_count, used_k, constraint_id: str) -> Dict:
        """Apply vehicle count constraints"""
        
        params = constraint.parameters
        constraints_added = 0
        
        if "min_vehicles" in params or "min" in params:
            min_vehicles = int(params.get("min_vehicles", params.get("min", 2)))
            prob += lpSum(used_k[k] for k in range(vehicle_count)) >= min_vehicles, f"MinVehicles_{constraint_id}"
            constraints_added += 1
            print(f"[Enhanced Applier] Applied minimum vehicles constraint: {min_vehicles}")
        
        if "max_vehicles" in params or "max" in params:
            max_vehicles = int(params.get("max_vehicles", params.get("max", vehicle_count)))
            prob += lpSum(used_k[k] for k in range(vehicle_count)) <= max_vehicles, f"MaxVehicles_{constraint_id}"
            constraints_added += 1
            print(f"[Enhanced Applier] Applied maximum vehicles constraint: {max_vehicles}")
        
        return {
            "success": True,
            "constraint_type": "vehicle_count",
            "mathematical_constraints_added": constraints_added,
            "details": f"Vehicle count constraints applied"
        }
    
    def _apply_multi_part_constraint(self, prob, constraint: ParsedConstraint, 
                                   nodes, vehicle_count, vehicle_capacity, demand, 
                                   used_k, x, u, constraint_id: str) -> Dict:
        """Apply multi-part constraints (combinations of constraints)"""
        
        params = constraint.parameters
        subtype = constraint.subtype
        constraints_added = 0
        details = []
        
        # Apply vehicle count part
        if "min_vehicles" in params:
            min_vehicles = int(params["min_vehicles"])
            prob += lpSum(used_k[k] for k in range(vehicle_count)) >= min_vehicles, f"MultiPart_MinVehicles_{constraint_id}"
            constraints_added += 1
            details.append(f"Min vehicles: {min_vehicles}")
        
        # Apply node constraint part
        if "nodes" in params and len(params["nodes"]) >= 2:
            nodes_list = params["nodes"]
            node_constraint_type = params.get("node_constraint_type", "grouping")
            
            if node_constraint_type == "separation":
                # Apply separation between the nodes
                for k in range(vehicle_count):
                    prob += (
                        lpSum(x[i, nodes_list[0], k] for i in nodes if i != nodes_list[0]) + 
                        lpSum(x[i, nodes_list[1], k] for i in nodes if i != nodes_list[1])
                    ) <= 1, f"MultiPart_Separation_{nodes_list[0]}_{nodes_list[1]}_Vehicle_{k}_{constraint_id}"
                    constraints_added += 1
                details.append(f"Separation: nodes {nodes_list[0]} and {nodes_list[1]}")
                
            elif node_constraint_type == "grouping":
                # Apply STRONG grouping between the nodes
                node1, node2 = nodes_list[0], nodes_list[1]
                
                # Method 1: Both nodes have same visited status for each vehicle
                for k in range(vehicle_count):
                    prob += (
                        lpSum(x[i, node1, k] for i in nodes if i != node1) == 
                        lpSum(x[i, node2, k] for i in nodes if i != node2)
                    ), f"MultiPart_Grouping_Same_{node1}_{node2}_Vehicle_{k}_{constraint_id}"
                    constraints_added += 1
                
                # Method 2: Cross-vehicle exclusion
                for k in range(vehicle_count):
                    for other_k in range(vehicle_count):
                        if k != other_k:
                            prob += (
                                lpSum(x[i, node1, k] for i in nodes if i != node1) + 
                                lpSum(x[i, node2, other_k] for i in nodes if i != node2)
                            ) <= 1, f"MultiPart_Grouping_Exclusive_{node1}_{node2}_V{k}_V{other_k}_{constraint_id}"
                            constraints_added += 1
                
                # Method 3: Strong coupling with auxiliary variables
                from pulp import LpVariable, LpBinary
                
                both_served_vars = {}
                for k in range(vehicle_count):
                    both_served_vars[k] = LpVariable(f"MultiPart_BothServed_{node1}_{node2}_V{k}_{constraint_id}", cat=LpBinary)
                    
                    # Force constraints
                    prob += (
                        lpSum(x[i, node1, k] for i in nodes if i != node1) >= both_served_vars[k]
                    ), f"MultiPart_Force1_{node1}_{node2}_V{k}_{constraint_id}"
                    constraints_added += 1
                    
                    prob += (
                        lpSum(x[i, node2, k] for i in nodes if i != node2) >= both_served_vars[k]
                    ), f"MultiPart_Force2_{node1}_{node2}_V{k}_{constraint_id}"
                    constraints_added += 1
                    
                    # Trigger constraints
                    prob += (
                        both_served_vars[k] >= lpSum(x[i, node1, k] for i in nodes if i != node1)
                    ), f"MultiPart_Trigger1_{node1}_{node2}_V{k}_{constraint_id}"
                    constraints_added += 1
                    
                    prob += (
                        both_served_vars[k] >= lpSum(x[i, node2, k] for i in nodes if i != node2)
                    ), f"MultiPart_Trigger2_{node1}_{node2}_V{k}_{constraint_id}"
                    constraints_added += 1
                
                # Only one vehicle can serve both nodes
                prob += (
                    lpSum(both_served_vars[k] for k in range(vehicle_count)) <= 1
                ), f"MultiPart_OnlyOne_{node1}_{node2}_{constraint_id}"
                constraints_added += 1
                
                details.append(f"STRONG grouping: nodes {node1} and {node2}")
        
        print(f"[Enhanced Applier] Applied multi-part constraint: {'; '.join(details)}")
        
        return {
            "success": True,
            "constraint_type": "multi_part",
            "mathematical_constraints_added": constraints_added,
            "details": f"Multi-part constraint: {'; '.join(details)}"
        }
    
    def _apply_priority_constraint(self, prob, constraint: ParsedConstraint, nodes, 
                                 vehicle_count, x, constraint_id: str) -> Dict:
        """Apply priority constraints (service order preferences)"""
        
        params = constraint.parameters
        node = int(params["node"])
        priority_level = params.get("priority_level", "high")
        
        # Priority constraints are typically handled in preprocessing or objective function
        # For now, we'll just log them
        print(f"[Enhanced Applier] Priority constraint noted: node {node} has {priority_level} priority")
        print(f"[Enhanced Applier] Note: Priority constraints typically require preprocessing or objective modification")
        
        return {
            "success": True,
            "constraint_type": "priority",
            "mathematical_constraints_added": 0,
            "details": f"Priority constraint noted for node {node} ({priority_level})",
            "warning": "Priority constraints require preprocessing or objective function modification"
        }
    
    def get_constraint_summary(self) -> Dict:
        """Get summary of applied constraints"""
        summary = {
            "total_applied": len(self.applied_constraints),
            "by_type": {},
            "complexity_levels": {"simple": 0, "medium": 0, "complex": 0},
            "parsing_methods": {}
        }
        
        for constraint in self.applied_constraints:
            # Count by type
            constraint_type = constraint.constraint_type
            summary["by_type"][constraint_type] = summary["by_type"].get(constraint_type, 0) + 1
            
            # Count by complexity
            complexity = constraint.complexity_level
            summary["complexity_levels"][complexity] = summary["complexity_levels"].get(complexity, 0) + 1
            
            # Count by parsing method
            method = constraint.parsing_method
            summary["parsing_methods"][method] = summary["parsing_methods"].get(method, 0) + 1
        
        return summary 