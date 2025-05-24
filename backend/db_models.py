from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime


Base = declarative_base()

class UploadedDataset(Base):
    __tablename__ = "uploaded_datasets"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    file_path = Column(String)
    file_type = Column(String)
    upload_time = Column(DateTime, default=datetime.now)

class Snapshot(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    snapshot_id = Column(String)
    dataset_id = Column(Integer, ForeignKey("uploaded_datasets.id"))
    file_path = Column(String)
    created_at = Column(DateTime, default=datetime.now)


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
    distance_matrix = Column(JSON)
    customer_data = Column(JSON)
    vehicle_data = Column(JSON)

    # Solver settings
    solver_type = Column(String(50), default='pulp')
    solver_params = Column(JSON)

    # Status
    status = Column(String(50), default='created')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    solved_at = Column(DateTime)

    # Relationships
    constraints = relationship("VRPConstraint", back_populates="problem", cascade="all, delete-orphan")
    solutions = relationship("VRPSolution", back_populates="problem", cascade="all, delete-orphan")


class VRPConstraint(Base):
    """Natural language constraints for VRP problems"""
    __tablename__ = 'vrp_constraints'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    original_prompt = Column(Text, nullable=False)
    normalized_prompt = Column(Text)
    constraint_type = Column(String(100))
    parameters = Column(JSON)
    mathematical_format = Column(JSON)

    parsing_method = Column(String(50))
    confidence = Column(Float, default=0.0)
    validation_status = Column(String(50), default='valid')
    validation_details = Column(JSON)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    applied_to_solver = Column(Boolean, default=False)

    problem = relationship("VRPProblem", back_populates="constraints")


class VRPSolution(Base):
    """Solutions for VRP problems"""
    __tablename__ = 'vrp_solutions'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    solution_name = Column(String(255))
    solver_used = Column(String(50))
    solve_time_seconds = Column(Float)

    objective_value = Column(Float)
    total_distance = Column(Float)
    total_time = Column(Float)
    vehicles_used = Column(Integer)

    routes = Column(JSON)
    route_details = Column(JSON)
    unserved_customers = Column(JSON)

    constraints_satisfied = Column(JSON)
    constraint_violations = Column(JSON)

    is_feasible = Column(Boolean, default=True)
    is_optimal = Column(Boolean, default=False)
    gap_percent = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    problem = relationship("VRPProblem", back_populates="solutions")


class VRPCustomer(Base):
    """Customer/location data for VRP problems"""
    __tablename__ = 'vrp_customers'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    customer_id = Column(String(100), nullable=False)
    customer_name = Column(String(255))

    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(Text)

    demand = Column(Float, default=0)
    service_time = Column(Float, default=0)

    earliest_time = Column(Integer)
    latest_time = Column(Integer)

    priority = Column(Integer, default=1)
    special_requirements = Column(JSON)

    is_depot = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class VRPVehicle(Base):
    """Vehicle data for VRP problems"""
    __tablename__ = 'vrp_vehicles'

    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('vrp_problems.id'), nullable=False)

    vehicle_id = Column(String(100), nullable=False)
    vehicle_name = Column(String(255))
    vehicle_type = Column(String(100))

    weight_capacity = Column(Float)
    volume_capacity = Column(Float)
    max_customers = Column(Integer)

    max_working_time = Column(Integer)
    start_time = Column(Integer)
    end_time = Column(Integer)

    fixed_cost = Column(Float, default=0)
    distance_cost = Column(Float, default=1)
    time_cost = Column(Float, default=0)

    start_location = Column(String(100))
    end_location = Column(String(100))

    special_capabilities = Column(JSON)
    restricted_areas = Column(JSON)

    is_available = Column(Boolean, default=True)


# ========================================
# DATABASE UTILITIES (updated)
# ========================================

def create_all_tables(engine):
    """Create all tables including new VRP tables"""
    Base.metadata.create_all(engine)
    print("✅ All tables created (including VRP tables)")


def create_vrp_tables_only(engine):
    """Create only VRP tables (for incremental migration)"""
    vrp_tables = [
        VRPProblem.__table__,
        VRPConstraint.__table__,
        VRPSolution.__table__,
        VRPCustomer.__table__,
        VRPVehicle.__table__
    ]

    for table in vrp_tables:
        table.create(engine, checkfirst=True)

    print("✅ VRP tables created")


# Migration helper
def migrate_existing_database(engine):
    """Migration script for existing databases"""
    try:
        # Try to create only new VRP tables
        create_vrp_tables_only(engine)
        print("✅ Database migration successful")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("You may need to run manual migration or recreate database")