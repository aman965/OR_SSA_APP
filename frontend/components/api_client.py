import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api"

def get_uploads():
    """Fetch all uploads from the API"""
    response = requests.get(f"{API_BASE_URL}/uploads/")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch uploads: {response.status_code}")
        return []

def get_snapshots():
    """Fetch all snapshots from the API"""
    response = requests.get(f"{API_BASE_URL}/snapshots/")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch snapshots: {response.status_code}")
        return []

def get_scenarios(snapshot_id=None):
    """Fetch scenarios, optionally filtered by snapshot_id"""
    url = f"{API_BASE_URL}/scenarios/"
    if snapshot_id:
        url += f"?snapshot={snapshot_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to fetch scenarios: {response.status_code}")
        return []

def create_upload(name, file):
    """Create a new upload"""
    files = {'file': file}
    data = {'name': name}
    response = requests.post(f"{API_BASE_URL}/uploads/", data=data, files=files)
    if response.status_code == 201:
        return response.json()
    else:
        st.error(f"Failed to create upload: {response.status_code}")
        return None

def create_snapshot(name, upload_id, description=None):
    """Create a new snapshot"""
    data = {
        'name': name,
        'dataset': upload_id
    }
    if description is not None:
        data['description'] = description
    response = requests.post(f"{API_BASE_URL}/snapshots/", json=data)
    if response.status_code == 201:
        return response.json()
    else:
        st.error(f"Failed to create snapshot: {response.status_code}")
        return None

def create_scenario(data):
    """Create a new scenario"""
    response = requests.post(f"{API_BASE_URL}/scenarios/", json=data)
    if response.status_code == 201:
        return response.json()
    else:
        st.error(f"Failed to create scenario: {response.status_code}")
        return None

def add_constraint_prompt(scenario_id: str, prompt: str) -> dict | None:
    """Add a constraint prompt to a scenario."""
    response = requests.post(
        f"{API_BASE_URL}/scenarios/{scenario_id}/add_constraint/",
        json={"prompt": prompt}
    )
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to add constraint: {response.status_code}")
        return None 