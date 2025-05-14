from backend.db_utils import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized successfully! Check for backend/app.db")