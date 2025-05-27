# Configuration Guide

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DATABASE_URL=sqlite:///db.sqlite3

# OpenAI Configuration (Optional - for advanced constraint parsing)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Media and File Storage
MEDIA_ROOT=./media
UPLOAD_MAX_SIZE=10485760  # 10MB in bytes

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

## Streamlit Secrets

Create `frontend/.streamlit/secrets.toml` for Streamlit-specific configuration:

```toml
[openai]
api_key = "your-openai-api-key-here"
model = "gpt-4o"

[database]
url = "sqlite:///backend/app.db"
```

## Installation Instructions

### Production Setup
```bash
pip install -r requirements.txt
```

### Development Setup
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Full Feature Setup (with optional enhancements)
```bash
pip install -r requirements.txt -r requirements-optional.txt
```

### Complete Development Setup
```bash
pip install -r requirements.txt -r requirements-dev.txt -r requirements-optional.txt
```

## Database Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Run Django migrations:
```bash
python manage.py migrate
```

3. Create a superuser (optional):
```bash
python manage.py createsuperuser
```

## Running the Application

From the root directory:
```bash
streamlit run frontend/main.py
```

The application will be available at `http://localhost:8501` 