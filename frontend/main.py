# ──────────────── frontend/main.py ────────────────
# Launch with:
#     streamlit run frontend/main.py
#
# Prereqs (once per clone):
#     python -m venv .venv
#     .venv\Scripts\activate      # <‑‑ PowerShell / Cmd
#     pip install -e .[frontend]
# ───────────────────────────────────────────────────

import os
import streamlit as st

# ── Initialise Django ─────────────────────────────
try:
    import django
    from django.core.management import call_command

    # Tell Django where its settings live (do this early!)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.django_settings")

    # Load settings, connect the ORM, register apps
    django.setup()

    # Auto‑apply any outstanding migrations (SQLite dev convenience)
    try:
        call_command("migrate", interactive=False, run_syncdb=True, verbosity=0)
    except Exception as mig_err:  # noqa: BLE001
        MIGRATION_ERROR = mig_err
        raise

    from backend.core.models import Upload  # noqa: E402  – safe after setup
    DJANGO_READY = True
except Exception as e:  # noqa: BLE001
    DJANGO_READY = False
    DJANGO_ERROR = e
# ──────────────────────────────────────────────────

# ===== Sidebar diagnostics =====
st.sidebar.markdown("### ⚙️ Diagnostic Info")
st.sidebar.write("Current working directory:", os.getcwd())

# Streamlit self‑check
st.sidebar.success("✅ Streamlit is working.")

# Django self‑check
if DJANGO_READY:
    st.sidebar.success(f"✅ Django initialised (v{django.get_version()})")
    st.sidebar.write("INSTALLED_APPS:", django.conf.settings.INSTALLED_APPS)
else:
    st.sidebar.error("❌ Django failed to initialise")
    st.sidebar.exception(DJANGO_ERROR)

# ===== Main UI =====
st.title("OR SaaS App – UI Shell")

# Discover extra Streamlit pages
try:
    pages_dir = os.path.join(os.path.dirname(__file__), "pages")
    available_pages = [f[:-3] for f in os.listdir(pages_dir) if f.endswith(".py")]
    st.sidebar.write("Available Pages:", available_pages)
except Exception as e:  # noqa: BLE001
    st.sidebar.error("❌ Error reading pages directory.")
    st.sidebar.exception(e)

# Simple proof the Upload model is usable
if DJANGO_READY:
    st.success(f"Django model import succeeded → {Upload.__name__}")
# ───────────────────────────────────────────────────
