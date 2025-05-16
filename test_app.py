import os
import sys
import subprocess
import time
import requests

def test_streamlit_app():
    """Test the Streamlit application by starting it and checking if it's accessible"""
    print("Starting Streamlit application...")
    
    process = subprocess.Popen(
        ["streamlit", "run", "frontend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(5)
    
    try:
        response = requests.get("http://localhost:8501")
        if response.status_code == 200:
            print("✅ Streamlit application is running successfully!")
        else:
            print(f"❌ Streamlit application returned status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Streamlit application")
    
    process.terminate()
    process.wait()
    
    print("Test completed.")

if __name__ == "__main__":
    test_streamlit_app()
