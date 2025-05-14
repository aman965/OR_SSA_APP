# OR SaaS App

A web-based Operations Research Software as a Service application built with Django, Streamlit, and SQLAlchemy.

## Features

- Dataset Upload & Management
- Snapshot Creation & Management
- Scenario Management
- Results Visualization

## Tech Stack

- Frontend: Streamlit
- Backend: Django + SQLAlchemy
- Database: SQLite
- File Storage: Local filesystem

## Project Structure

```
or_saas_app/
├── backend/
│   ├── core/              # Django app
│   ├── orsaas_backend/    # Django project settings
│   ├── db_models.py       # SQLAlchemy models
│   └── db_utils.py        # Database utilities
├── frontend/
│   ├── pages/             # Streamlit pages
│   ├── components/        # Reusable components
│   └── main.py           # Streamlit entry point
└── media/
    ├── uploads/          # Uploaded datasets
    └── snapshots/        # Dataset snapshots
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
cd backend
python manage.py migrate
```

4. Run the application:
```bash
streamlit run frontend/main.py
```

## Development

- The application uses both Django ORM (for web API) and SQLAlchemy (for file operations)
- Streamlit is used for rapid UI development
- File uploads are stored in `media/uploads/`
- Snapshots are stored in `media/snapshots/`

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 