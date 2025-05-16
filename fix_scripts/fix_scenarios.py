#!/usr/bin/env python3
"""
Comprehensive Fix for Scenarios Stuck in "Solving" State

This script provides a robust solution to fix scenarios stuck in "solving" state
by directly modifying the SQLite database and fixing directory structures.
It works in any environment regardless of Django setup or orsaas_core module.
"""

import os
import sys
import sqlite3
import json
import shutil
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("=" * 80)
    print(title.center(80))
    print("=" * 80)

def reset_scenarios_with_sqlite():
    """Reset all scenarios to 'created' status using direct SQLite access"""
    try:
        print("Resetting scenarios using SQLite...")
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend', 'db.sqlite3')
        
        if not os.path.exists(db_path):
            print(f"Database not found at {db_path}")
            return False
            
        print(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get current scenario statuses
        cursor.execute("SELECT id, name, status FROM core_scenario")
        scenarios = cursor.fetchall()
        print(f"Found {len(scenarios)} scenarios in database")
        
        for scenario_id, name, status in scenarios:
            print(f"Scenario {scenario_id} ({name}): Current status = {status}")
        
        # Reset all scenarios to 'created' status
        cursor.execute("UPDATE core_scenario SET status = 'created'")
        updated_rows = cursor.rowcount
        conn.commit()
        
        print(f"Reset {updated_rows} scenarios to 'created' status")
        conn.close()
        return updated_rows > 0
    except Exception as e:
        print(f"SQLite reset failed: {str(e)}")
        return False

def fix_scenario_directories():
    """Fix scenario directories by ensuring proper structure and copying files if needed"""
    try:
        print("Checking scenario directories...")
        media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'media')
        scenarios_dir = os.path.join(media_dir, 'scenarios')
        
        if not os.path.exists(scenarios_dir):
            print(f"Scenarios directory not found at {scenarios_dir}")
            os.makedirs(scenarios_dir, exist_ok=True)
            print(f"Created scenarios directory at {scenarios_dir}")
            return True
            
        scenario_dirs = [d for d in os.listdir(scenarios_dir) if os.path.isdir(os.path.join(scenarios_dir, d))]
        print(f"Found {len(scenario_dirs)} scenario directories")
        
        for scenario_dir_name in scenario_dirs:
            scenario_dir = os.path.join(scenarios_dir, scenario_dir_name)
            output_dir = os.path.join(scenario_dir, 'outputs')
            
            # Create outputs directory if it doesn't exist
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                print(f"Created outputs directory for scenario {scenario_dir_name}")
            
            # Fix permissions on directories
            os.chmod(scenario_dir, 0o755)
            os.chmod(output_dir, 0o755)
            
            # Check for model.lp file and copy to outputs directory if needed
            model_lp = os.path.join(scenario_dir, 'model.lp')
            output_model_lp = os.path.join(output_dir, 'model.lp')
            if os.path.exists(model_lp) and not os.path.exists(output_model_lp):
                shutil.copy2(model_lp, output_model_lp)
                print(f"Copied model.lp to outputs directory for scenario {scenario_dir_name}")
            
            # Check for solution_summary.json file and copy to outputs directory if needed
            solution_file = os.path.join(scenario_dir, 'solution_summary.json')
            output_solution_file = os.path.join(output_dir, 'solution_summary.json')
            if os.path.exists(solution_file) and not os.path.exists(output_solution_file):
                shutil.copy2(solution_file, output_solution_file)
                print(f"Copied solution_summary.json to outputs directory for scenario {scenario_dir_name}")
                
            # Check for failure_summary.json file and copy to outputs directory if needed
            failure_file = os.path.join(scenario_dir, 'failure_summary.json')
            output_failure_file = os.path.join(output_dir, 'failure_summary.json')
            if os.path.exists(failure_file) and not os.path.exists(output_failure_file):
                shutil.copy2(failure_file, output_failure_file)
                print(f"Copied failure_summary.json to outputs directory for scenario {scenario_dir_name}")
        
        return True
    except Exception as e:
        print(f"Directory fix failed: {str(e)}")
        return False

def check_streamlit_app():
    """Check if Streamlit app is running and kill it if needed"""
    try:
        import psutil
        
        print("Checking for running Streamlit processes...")
        streamlit_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'streamlit' in proc.info['name'].lower() or any('streamlit' in cmd.lower() for cmd in proc.info['cmdline'] if cmd):
                    streamlit_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if streamlit_processes:
            print(f"Found {len(streamlit_processes)} Streamlit processes running")
            for proc in streamlit_processes:
                print(f"PID: {proc.info['pid']}, Command: {' '.join(proc.info['cmdline'])}")
            
            print("\nTo restart the Streamlit app, you need to kill these processes first.")
            print("Run the following commands:")
            for proc in streamlit_processes:
                print(f"kill -9 {proc.info['pid']}")
        else:
            print("No Streamlit processes found running")
        
        return True
    except ImportError:
        print("psutil module not found. Cannot check for running Streamlit processes.")
        print("To install: pip install psutil")
        return False
    except Exception as e:
        print(f"Error checking Streamlit processes: {str(e)}")
        return False

def main():
    """Main function to fix scenarios stuck in 'solving' state"""
    print_header("COMPREHENSIVE SCENARIO FIX TOOL")
    print("This script will fix scenarios stuck in 'solving' state by:")
    print("1. Resetting all scenarios to 'created' status in the database")
    print("2. Fixing directory structures and file permissions")
    print("3. Checking for running Streamlit processes")
    print()
    
    # Step 1: Reset scenarios in database
    sqlite_success = reset_scenarios_with_sqlite()
    
    # Step 2: Fix directory structures
    dir_success = fix_scenario_directories()
    
    # Step 3: Check Streamlit app
    app_checked = check_streamlit_app()
    
    print_header("FIX COMPLETE")
    print("Results:")
    print(f"- Database reset: {'SUCCESS' if sqlite_success else 'FAILED'}")
    print(f"- Directory fix: {'SUCCESS' if dir_success else 'FAILED'}")
    print(f"- App check: {'SUCCESS' if app_checked else 'FAILED'}")
    print()
    print("Next steps:")
    print("1. Kill any running Streamlit processes (see above for commands)")
    print("2. Restart the Streamlit app: streamlit run frontend/main.py")
    print("3. Verify that scenarios can be run successfully")
    print("4. Check that model.lp files are created in the outputs directory")
    print()
    print("If you still see issues, please contact support.")

if __name__ == "__main__":
    main()
