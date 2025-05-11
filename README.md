# OR SaaS App

This project consists of a Django backend and Streamlit frontend for an Operations Research SaaS application.

## Project Structure

- `backend/`: Django backend application
- `frontend/`: Streamlit frontend application
- `media/`: Directory for storing uploaded files and generated content
  - `uploads/`: User uploaded files
  - `snapshots/`: Generated snapshots
  - `scenarios/`: Scenario files

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the backend:
```bash
cd backend
python manage.py runserver
```

3. Run the frontend:
```bash
cd frontend
streamlit run main.py
``` 