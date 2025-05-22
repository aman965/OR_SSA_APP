# OR-SSA Application

A Streamlit-based application for Operations Research Scenario Simulation and Analysis.

## Overview

This application provides a user-friendly interface for:
- Uploading and managing datasets
- Creating snapshots of datasets
- Building and solving optimization scenarios
- Analyzing results with interactive visualizations

## Architecture

The application follows a clean architecture pattern:

```
OR_SSA_APP/
├── backend/                 # Django backend
│   ├── core/               # Core business logic
│   │   ├── models.py       # Django models
│   │   ├── views.py        # API endpoints
│   │   └── serializers.py  # Data serialization
│   ├── repositories/       # Data access layer
│   │   └── scenario_repo.py # Scenario repository
│   ├── solver/            # Optimization solver
│   │   └── vrp_solver.py  # VRP implementation
│   └── tasks.py           # Background tasks
├── frontend/              # Streamlit frontend
│   ├── pages/            # Streamlit pages
│   └── components/       # Reusable components
└── requirements.txt      # Python dependencies
```

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis (for Celery)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/OR_SSA_APP.git
   cd OR_SSA_APP
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   python manage.py migrate
   ```

6. Start Redis server:
   ```bash
   redis-server
   ```

7. Start Celery worker:
   ```bash
   celery -A backend worker -l info
   ```

8. Start Celery beat (for scheduled tasks):
   ```bash
   celery -A backend beat -l info
   ```

9. Run the development server:
   ```bash
   python manage.py runserver
   ```

10. In a separate terminal, start Streamlit:
    ```bash
    streamlit run frontend/app.py
    ```

## Usage

### Dataset Management

1. Navigate to the Upload page
2. Click "Upload Dataset" to select a CSV file
3. Provide a name and description
4. Click "Upload" to process the dataset

### Scenario Building

1. Go to the Scenario Builder page
2. Select a dataset snapshot
3. Configure scenario parameters:
   - param1: Parameter 1 description
   - param2: Parameter 2 description
   - param3: Parameter 3 description
   - param4: Parameter 4 description
   - param5: Parameter 5 description
4. Add constraints using natural language
5. Click "Solve" to start optimization

### Results Analysis

1. View the Results page
2. Select a solved scenario
3. Explore:
   - Solution summary
   - Route visualizations
   - Performance metrics
   - Constraint analysis

## Development

### Running Tests

```bash
python manage.py test
```

### Code Style

The project follows PEP 8 guidelines. Use `black` for code formatting:

```bash
black .
```

### Database Migrations

To create a new migration:

```bash
python manage.py makemigrations
```

To apply migrations:

```bash
python manage.py migrate
```

## API Documentation

### Endpoints

#### Uploads

- `GET /api/uploads/` - List all uploads
- `POST /api/uploads/` - Create a new upload
- `GET /api/uploads/{id}/` - Get upload details
- `DELETE /api/uploads/{id}/` - Delete an upload

#### Snapshots

- `GET /api/snapshots/` - List all snapshots
- `POST /api/snapshots/` - Create a new snapshot
- `GET /api/snapshots/{id}/` - Get snapshot details
- `DELETE /api/snapshots/{id}/` - Delete a snapshot

#### Scenarios

- `GET /api/scenarios/` - List all scenarios
- `POST /api/scenarios/` - Create a new scenario
- `GET /api/scenarios/{id}/` - Get scenario details
- `DELETE /api/scenarios/{id}/` - Delete a scenario
- `POST /api/scenarios/{id}/add_constraint/` - Add a constraint

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 