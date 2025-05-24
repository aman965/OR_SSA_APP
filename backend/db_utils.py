from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
from typing import Generator

# Import your models
from backend.db_models import Base, VRPProblem, VRPConstraint, VRPSolution, VRPCustomer, VRPVehicle


# Get the absolute path to the database file
db_path = os.path.join(os.path.dirname(__file__), "app.db")
DATABASE_URL = f"sqlite:///{db_path}"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)

def get_session() -> Session:
    """Get a new database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e


class DatabaseManager:
    """Enhanced database manager with VRP support"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///orsaas.db')
        self.engine = create_engine(self.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print("✅ All database tables created")

    def migrate_for_vrp(self):
        """Migration for adding VRP tables to existing database"""
        try:
            # Create only VRP tables
            vrp_tables = [
                VRPProblem.__table__,
                VRPConstraint.__table__,
                VRPSolution.__table__,
                VRPCustomer.__table__,
                VRPVehicle.__table__
            ]

            for table in vrp_tables:
                table.create(self.engine, checkfirst=True)

            print("✅ VRP tables migration completed")
            return True
        except Exception as e:
            print(f"❌ VRP migration failed: {e}")
            return False

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with proper cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# ========================================
# VRP-SPECIFIC DATABASE OPERATIONS
# ========================================

class VRPDatabaseOperations:
    """Database operations specific to VRP functionality"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_vrp_problem(self, problem_data: dict) -> int:
        """Create a new VRP problem"""
        with self.db_manager.get_session() as session:
            problem = VRPProblem(
                name=problem_data['name'],
                description=problem_data.get('description', ''),
                num_vehicles=problem_data['num_vehicles'],
                depot_location=problem_data.get('depot_location', ''),
                distance_matrix=problem_data.get('distance_matrix'),
                customer_data=problem_data.get('customer_data'),
                vehicle_data=problem_data.get('vehicle_data'),
                solver_type=problem_data.get('solver_type', 'pulp')
            )
            session.add(problem)
            session.flush()  # Get the ID before commit
            problem_id = problem.id
            session.commit()
            return problem_id

    def get_vrp_problem(self, problem_id: int) -> dict:
        """Get VRP problem with all related data"""
        with self.db_manager.get_session() as session:
            problem = session.query(VRPProblem).filter(VRPProblem.id == problem_id).first()
            if not problem:
                return None

            return {
                'problem': {
                    'id': problem.id,
                    'name': problem.name,
                    'description': problem.description,
                    'num_vehicles': problem.num_vehicles,
                    'depot_location': problem.depot_location,
                    'distance_matrix': problem.distance_matrix,
                    'customer_data': problem.customer_data,
                    'vehicle_data': problem.vehicle_data,
                    'status': problem.status,
                    'created_at': problem.created_at.isoformat() if problem.created_at else None
                },
                'constraints': [
                    {
                        'id': c.id,
                        'original_prompt': c.original_prompt,
                        'constraint_type': c.constraint_type,
                        'parameters': c.parameters,
                        'is_active': c.is_active
                    }
                    for c in problem.constraints
                ],
                'solutions': [
                    {
                        'id': s.id,
                        'solution_name': s.solution_name,
                        'objective_value': s.objective_value,
                        'total_distance': s.total_distance,
                        'vehicles_used': s.vehicles_used,
                        'created_at': s.created_at.isoformat() if s.created_at else None
                    }
                    for s in problem.solutions
                ]
            }

    def save_constraints(self, problem_id: int, processed_constraints: list) -> bool:
        """Save processed constraints to database"""
        try:
            with self.db_manager.get_session() as session:
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
                        validation_status='valid' if constraint_data.get('validation', {}).get('is_valid',
                                                                                               True) else 'invalid',
                        validation_details=constraint_data.get('validation', {})
                    )
                    session.add(constraint)
                session.commit()
            return True
        except Exception as e:
            print(f"❌ Failed to save constraints: {e}")
            return False

    def save_solution(self, problem_id: int, solution_data: dict) -> int:
        """Save VRP solution to database"""
        with self.db_manager.get_session() as session:
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
            session.flush()
            solution_id = solution.id
            session.commit()
            return solution_id

    def get_all_problems(self) -> list:
        """Get list of all VRP problems"""
        with self.db_manager.get_session() as session:
            problems = session.query(VRPProblem).all()
            return [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description,
                    'num_vehicles': p.num_vehicles,
                    'status': p.status,
                    'created_at': p.created_at.isoformat() if p.created_at else None,
                    'constraint_count': len(p.constraints),
                    'solution_count': len(p.solutions)
                }
                for p in problems
            ]

    def delete_problem(self, problem_id: int) -> bool:
        """Delete VRP problem and all related data"""
        try:
            with self.db_manager.get_session() as session:
                problem = session.query(VRPProblem).filter(VRPProblem.id == problem_id).first()
                if problem:
                    session.delete(problem)  # Cascading will delete related records
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"❌ Failed to delete problem: {e}")
            return False


# ========================================
# INITIALIZE DATABASE SYSTEM
# ========================================

# Global database manager instance
db_manager = DatabaseManager()
vrp_db = VRPDatabaseOperations(db_manager)


def initialize_database():
    """Initialize database for the entire application"""
    try:
        # Try migration first (for existing databases)
        migration_success = db_manager.migrate_for_vrp()

        if not migration_success:
            # Create all tables from scratch
            db_manager.create_tables()

        print("✅ Database initialization completed")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


# For backward compatibility with your existing code
def get_session():
    """Get database session (compatible with existing code)"""
    return db_manager.get_session()


def get_engine():
    """Get database engine (compatible with existing code)"""
    return db_manager.engine


# ========================================
# MIGRATION SCRIPT (run this once)
# ========================================

def run_migration():
    """Run this once to add VRP tables to existing database"""
    print("🔄 Starting VRP migration...")

    try:
        success = db_manager.migrate_for_vrp()
        if success:
            print("✅ Migration completed successfully!")
            print("Your existing data is preserved.")
            print("New VRP tables have been added.")
        else:
            print("❌ Migration failed. Check the error messages above.")
    except Exception as e:
        print(f"❌ Migration error: {e}")


if __name__ == "__main__":
    # Run migration when this file is executed directly
    run_migration()