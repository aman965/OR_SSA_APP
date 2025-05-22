# Development Guide

## Overview

This document provides guidelines and best practices for developing the OR-SSA application.

## Architecture

The application follows a clean architecture pattern with the following layers:

1. **Presentation Layer** (Streamlit)
   - User interface components
   - Page layouts
   - API client

2. **Application Layer** (Django)
   - API endpoints
   - ViewSets
   - Serializers
   - Background tasks

3. **Domain Layer** (Django)
   - Models
   - Business logic
   - Validation rules

4. **Infrastructure Layer** (Django)
   - Repository pattern
   - Database access
   - File system operations

## Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Configure your IDE:
   - Use Python 3.8+
   - Enable type checking
   - Use black for formatting
   - Use isort for import sorting

## Code Style

### Python

- Follow PEP 8 guidelines
- Use type hints
- Maximum line length: 88 characters
- Use black for formatting
- Use isort for import sorting
- Use flake8 for linting

Example:
```python
from typing import Final, List, Optional

from django.db import models
from django.utils import timezone


class MyModel(models.Model):
    """Model description."""

    name: Final[str] = models.CharField(max_length=100)
    created_at: Final[datetime] = models.DateTimeField(auto_now_add=True)

    def get_items(self) -> List[str]:
        """Get items.

        Returns:
            List of items.
        """
        return [item.name for item in self.items.all()]
```

### JavaScript/TypeScript

- Use ESLint
- Use Prettier
- Use TypeScript
- Maximum line length: 88 characters

Example:
```typescript
interface Props {
  name: string;
  items: string[];
}

const MyComponent: React.FC<Props> = ({ name, items }) => {
  return (
    <div>
      <h1>{name}</h1>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
};
```

## Testing

### Python Tests

- Use Django's test framework
- Use pytest for additional features
- Use factory_boy for test data
- Use coverage.py for coverage reports

Example:
```python
from django.test import TestCase
from factory import Faker

from core.models import MyModel
from core.factories import MyModelFactory


class MyModelTest(TestCase):
    """Test cases for MyModel."""

    def setUp(self):
        """Set up test data."""
        self.model = MyModelFactory()

    def test_something(self):
        """Test something."""
        self.assertEqual(self.model.name, "test")
```

### JavaScript Tests

- Use Jest
- Use React Testing Library
- Use MSW for API mocking

Example:
```typescript
import { render, screen } from '@testing-library/react';
import { MyComponent } from './MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent name="test" items={['item1', 'item2']} />);
    expect(screen.getByText('test')).toBeInTheDocument();
  });
});
```

## Database

### Migrations

1. Create a migration:
   ```bash
   python manage.py makemigrations
   ```

2. Apply migrations:
   ```bash
   python manage.py migrate
   ```

3. Show migration status:
   ```bash
   python manage.py showmigrations
   ```

### Best Practices

- Keep migrations small and focused
- Test migrations on a copy of production data
- Use `RunPython` for complex migrations
- Use `RunSQL` for raw SQL when needed
- Document migration dependencies

## Background Tasks

### Celery

- Use Celery for background tasks
- Use Redis as message broker
- Use Celery Beat for scheduled tasks
- Use task routing for different queues

Example:
```python
from celery import shared_task
from django.db import transaction

@shared_task(bind=True, max_retries=3)
def my_task(self, arg1: str, arg2: int) -> None:
    """Task description."""
    try:
        with transaction.atomic():
            # Task logic
            pass
    except Exception as e:
        self.retry(exc=e, countdown=60)
```

### Best Practices

- Use transactions for data consistency
- Handle task failures gracefully
- Use task routing for different priorities
- Monitor task execution
- Use task timeouts

## API Development

### REST API

- Follow REST principles
- Use proper HTTP methods
- Use proper status codes
- Use proper content types
- Use proper authentication

Example:
```python
from rest_framework import viewsets, status
from rest_framework.response import Response

class MyViewSet(viewsets.ModelViewSet):
    """ViewSet description."""

    def create(self, request, *args, **kwargs):
        """Create a new instance."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
```

### Best Practices

- Use ViewSets for CRUD operations
- Use Serializers for data validation
- Use Permissions for access control
- Use Pagination for large datasets
- Use Filtering for data filtering
- Use Ordering for data sorting
- Use Throttling for rate limiting

## Frontend Development

### Streamlit

- Use components for reusability
- Use pages for organization
- Use session state for persistence
- Use caching for performance

Example:
```python
import streamlit as st
from frontend.components.api_client import get_data

def main():
    """Main function."""
    st.title("My App")
    data = get_data()
    st.write(data)
```

### Best Practices

- Use components for reusability
- Use pages for organization
- Use session state for persistence
- Use caching for performance
- Use error handling
- Use loading states
- Use proper styling

## Deployment

### Development

1. Run development server:
   ```bash
   python manage.py runserver
   ```

2. Run Streamlit:
   ```bash
   streamlit run frontend/app.py
   ```

3. Run Celery worker:
   ```bash
   celery -A backend worker -l info
   ```

4. Run Celery beat:
   ```bash
   celery -A backend beat -l info
   ```

### Production

1. Set environment variables:
   ```bash
   export DJANGO_SETTINGS_MODULE=backend.settings
   export DJANGO_SECRET_KEY=your-secret-key
   export DATABASE_URL=your-database-url
   export REDIS_URL=your-redis-url
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Collect static files:
   ```bash
   python manage.py collectstatic
   ```

4. Run with gunicorn:
   ```bash
   gunicorn backend.wsgi:application
   ```

5. Run with supervisor:
   ```bash
   supervisorctl start all
   ```

## Monitoring

### Logging

- Use Django's logging framework
- Use proper log levels
- Use proper log formatting
- Use proper log handlers

Example:
```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    """Function description."""
    logger.info("Function called")
    try:
        # Function logic
        pass
    except Exception as e:
        logger.exception("Function failed")
        raise
```

### Metrics

- Use Prometheus for metrics
- Use Grafana for visualization
- Use proper metric names
- Use proper metric labels

Example:
```python
from prometheus_client import Counter, Histogram

request_count = Counter('request_count', 'Request count')
request_latency = Histogram('request_latency', 'Request latency')

def my_view(request):
    """View description."""
    request_count.inc()
    with request_latency.time():
        # View logic
        pass
```

## Security

### Authentication

- Use Django's authentication framework
- Use proper password hashing
- Use proper session management
- Use proper token management

### Authorization

- Use Django's permission system
- Use proper role management
- Use proper access control
- Use proper resource protection

### Data Protection

- Use proper data encryption
- Use proper data sanitization
- Use proper data validation
- Use proper data access control

## Performance

### Database

- Use proper indexing
- Use proper query optimization
- Use proper connection pooling
- Use proper caching

### API

- Use proper pagination
- Use proper filtering
- Use proper ordering
- Use proper caching

### Frontend

- Use proper code splitting
- Use proper lazy loading
- Use proper caching
- Use proper compression

## Troubleshooting

### Common Issues

1. Database connection issues:
   - Check database URL
   - Check database credentials
   - Check database permissions

2. Redis connection issues:
   - Check Redis URL
   - Check Redis credentials
   - Check Redis permissions

3. Celery issues:
   - Check Celery configuration
   - Check Celery logs
   - Check Celery status

4. API issues:
   - Check API logs
   - Check API status
   - Check API response

### Debugging

1. Use Django debug toolbar
2. Use Django shell
3. Use Python debugger
4. Use logging
5. Use monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 