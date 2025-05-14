# Run this app from the frontend directory using: streamlit run main.py
import sys
import os
from pathlib import Path

# Add project root to Python path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

import streamlit as st
from backend.db_utils import init_db

# Initialize database
try:
    init_db()
    st.sidebar.success("✅ Database initialized successfully")
except Exception as e:
    st.sidebar.error("❌ Database initialization failed")
    st.sidebar.exception(e)

try:
    st.sidebar.markdown("### 🛠 Diagnostic Info")
    st.sidebar.write("Current working directory:", os.getcwd())
    pages_dir = os.path.join(os.path.dirname(__file__), "pages")
    st.sidebar.write("Streamlit pages found:", os.listdir(pages_dir))
except Exception as e:
    st.sidebar.error("❌ Error reading pages directory.")
    st.sidebar.exception(e)

try:
    st.sidebar.success("✅ Streamlit is working.")
except Exception as e:
    st.sidebar.error("❌ Streamlit import failed.")
    raise e

try:
    import django
    st.sidebar.info("ℹ️ Django is installed, version: " + django.get_version())
except ImportError:
    st.sidebar.warning("⚠️ Django not used or not installed.")

st.title("OR SaaS App – UI Shell")

pages_dir = os.path.join(os.path.dirname(__file__), "pages")
available_pages = [f[:-3] for f in os.listdir(pages_dir) if f.endswith(".py")]
st.sidebar.write("Available Pages:", available_pages) 