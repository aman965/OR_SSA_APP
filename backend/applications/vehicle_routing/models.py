# backend/applications/vehicle_routing/models.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()


class VRPProblem(Base):
    """Main VRP problem instance"""
    __tablename__ = 'vrp_problems'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Problem configuration
    num_vehicles = Column(Integer, nullable=False, default=1)
    depot_location = Column(String(255))

    # Problem data (JSON format)
    distance_matrix = Column(JSON)  # Distance matrix between locations
    customer_data = Column(JSON)  # Customer locations, demands, time windows
    vehicle_data = Column(JSON)  # Vehicle capacities, costs, constraints

    # Solver settings
    solver_type = Column(String(50), default='pulp')  # 'pulp', 'ortools', 'gurobi'
    solver_params = Column(JSON)  # Solver-specific parameters

    # Status
    status = Column(String(50), default='created')  # 'created', 'solving', 'solved', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    solved_at = Column(DateTime)

    # Relationships
    constraints = relationship("VRPConstraint", back_populates="problem", cascade="all, delete-orphan")
    solutions = relationship("VRPSolution", back_populates="problem", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'num_vehicles': self.num_vehicles,
            'depot_location': self.depot_location,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'constraint_count': len(self.constraints) if self.constraints else 0,
            'solution_count': len(self.solutions) if self.solutions else 0
        }


class VRPConstraint(Base):
    """Natural language constraints for VRP problems"""
    __tablename__ = 'vrp_constraints'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    # Original constraint
    original_prompt = Column(Text, nullable=False)
    normalized_prompt = Column(Text)

    # Parsed constraint
    constraint_type = Column(String(100))  # 'capacity', 'time_window', 'distance', etc.
    parameters = Column(JSON)  # Extracted parameters
    mathematical_format = Column(JSON)  # Mathematical representation

    # Processing metadata
    parsing_method = Column(String(50))  # 'pattern_matching', 'llm_parsing'
    confidence = Column(Float, default=0.0)
    validation_status = Column(String(50), default='valid')  # 'valid', 'invalid', 'warning'
    validation_details = Column(JSON)  # Validation errors/warnings

    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_to_solver = Column(Boolean, default=False)

    # Relationships
    problem = relationship("VRPProblem", back_populates="constraints")

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'original_prompt': self.original_prompt,
            'constraint_type': self.constraint_type,
            'parameters': self.parameters,
            'parsing_method': self.parsing_method,
            'confidence': self.confidence,
            'validation_status': self.validation_status,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VRPSolution(Base):
    """Solutions for VRP problems"""
    __tablename__ = 'vrp_solutions'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    # Solution metadata
    solution_name = Column(String(255))
    solver_used = Column(String(50))
    solve_time_seconds = Column(Float)

    # Solution quality
    objective_value = Column(Float)  # Total distance/cost
    total_distance = Column(Float)  # Total distance traveled
    total_time = Column(Float)  # Total time
    vehicles_used = Column(Integer)  # Number of vehicles actually used

    # Solution data
    routes = Column(JSON)  # Route for each vehicle
    route_details = Column(JSON)  # Detailed route information
    unserved_customers = Column(JSON)  # Customers that couldn't be served

    # Constraint satisfaction
    constraints_satisfied = Column(JSON)  # Which constraints were satisfied
    constraint_violations = Column(JSON)  # Any constraint violations

    # Status
    is_feasible = Column(Boolean, default=True)
    is_optimal = Column(Boolean, default=False)
    gap_percent = Column(Float)  # Optimality gap for MIP solvers

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    problem = relationship("VRPProblem", back_populates="solutions")

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'solution_name': self.solution_name,
            'solver_used': self.solver_used,
            'solve_time_seconds': self.solve_time_seconds,
            'objective_value': self.objective_value,
            'total_distance': self.total_distance,
            'vehicles_used': self.vehicles_used,
            'is_feasible': self.is_feasible,
            'is_optimal': self.is_optimal,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class VRPCustomer(Base):
    """Customer/location data for VRP problems"""
    __tablename__ = 'vrp_customers'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    # Customer identification
    customer_id = Column(String(100), nullable=False)  # User-defined ID
    customer_name = Column(String(255))

    # Location
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(Text)

    # Demand and constraints
    demand = Column(Float, default=0)
    service_time = Column(Float, default=0)  # Time to serve customer

    # Time windows
    earliest_time = Column(Integer)  # Minutes from start of day
    latest_time = Column(Integer)  # Minutes from start of day

    # Priority and special requirements
    priority = Column(Integer, default=1)  # 1=normal, 2=high, 3=critical
    special_requirements = Column(JSON)  # Vehicle type requirements, etc.

    # Status
    is_depot = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'demand': self.demand,
            'service_time': self.service_time,
            'earliest_time': self.earliest_time,
            'latest_time': self.latest_time,
            'priority': self.priority,
            'is_depot': self.is_depot,
            'is_active': self.is_active
        }


class VRPVehicle(Base):
    """Vehicle data for VRP problems"""
    __tablename__ = 'vrp_vehicles'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    # Vehicle identification
    vehicle_id = Column(String(100), nullable=False)
    vehicle_name = Column(String(255))
    vehicle_type = Column(String(100))

    # Capacity constraints
    weight_capacity = Column(Float)
    volume_capacity = Column(Float)
    max_customers = Column(Integer)

    # Time constraints
    max_working_time = Column(Integer)  # Minutes
    start_time = Column(Integer)  # Minutes from start of day
    end_time = Column(Integer)  # Minutes from start of day

    # Cost parameters
    fixed_cost = Column(Float, default=0)  # Fixed cost to use vehicle
    distance_cost = Column(Float, default=1)  # Cost per unit distance
    time_cost = Column(Float, default=0)  # Cost per unit time

    # Location constraints
    start_location = Column(String(100))  # Can start from different depot
    end_location = Column(String(100))  # Can end at different location

    # Special capabilities
    special_capabilities = Column(JSON)  # Refrigeration, crane, etc.
    restricted_areas = Column(JSON)  # Areas this vehicle cannot visit

    # Status
    is_available = Column(Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'vehicle_id': self.vehicle_id,
            'vehicle_name': self.vehicle_name,
            'vehicle_type': self.vehicle_type,
            'weight_capacity': self.weight_capacity,
            'volume_capacity': self.volume_capacity,
            'max_working_time': self.max_working_time,
            'fixed_cost': self.fixed_cost,
            'distance_cost': self.distance_cost,
            'is_available': self.is_available
        }


# Utility functions for working with the models

def create_vrp_tables(engine):
    """Create all VRP tables"""
    Base.metadata.create_all(engine)


def get_problem_with_details(session, problem_id: int):
    """Get a VRP problem with all related data"""
    problem = session.query(VRPProblem).filter(VRPProblem.id == problem_id).first()
    if not problem:
        return None

    return {
        'problem': problem.to_dict(),
        'constraints': [c.to_dict() for c in problem.constraints],
        'solutions': [s.to_dict() for s in problem.solutions],
        'customers': session.query(VRPCustomer).filter(VRPCustomer.problem_id == problem_id).all(),
        'vehicles': session.query(VRPVehicle).filter(VRPVehicle.problem_id == problem_id).all()
    }


def save_processed_constraints(session, problem_id: int, processed_constraints: list):
    """Save processed constraints to database"""
    for constraint_data in processed_constraints:
        constraint = VRPConstraint(
            problem_id=problem_id,
            original_prompt=constraint_data.get('original_prompt', ''),
            normalized_prompt=constraint_data.get('normalized_prompt', ''),
            constraint_type=constraint_data.get('constraint_type', ''),
            parameters=constraint_data.get('parameters', {}),
            mathematical_format=constraint_data.get('mathematical_format', {}),
            parsing_method=constraint_data.get('parsing_method', ''),
            confidence=constraint_data.get('confidence', 0.0),
            validation_status='valid' if constraint_data.get('validation', {}).get('is_valid', True) else 'invalid',
            validation_details=constraint_data.get('validation', {})
        )
        session.add(constraint)

    session.commit()


def save_solution(session, problem_id: int, solution_data: dict):
    """Save VRP solution to database"""
    solution = VRPSolution(
        problem_id=problem_id,
        solution_name=solution_data.get('name', f'Solution_{datetime.now().strftime("%Y%m%d_%H%M")}'),
        solver_used=solution_data.get('solver', 'pulp'),
        solve_time_seconds=solution_data.get('solve_time', 0),
        objective_value=solution_data.get('objective_value', 0),
        total_distance=solution_data.get('total_distance', 0),
        total_time=solution_data.get('total_time', 0),
        vehicles_used=solution_data.get('vehicles_used', 0),
        routes=solution_data.get('routes', []),
        route_details=solution_data.get('route_details', {}),
        is_feasible=solution_data.get('is_feasible', True),
        is_optimal=solution_data.get('is_optimal', False),
        gap_percent=solution_data.get('gap_percent', 0),
        constraints_satisfied=solution_data.get('constraints_satisfied', {}),
        constraint_violations=solution_data.get('constraint_violations', [])
    )

    session.add(solution)
    session.commit()
    return solution.id