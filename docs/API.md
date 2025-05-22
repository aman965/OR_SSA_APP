# API Documentation

## Overview

The OR-SSA API provides endpoints for managing datasets, snapshots, and scenarios. All endpoints are RESTful and return JSON responses.

## Authentication

All API endpoints require authentication. Use Django's session authentication or token authentication.

### Session Authentication

Include the session cookie in your requests. This is automatically handled by the browser.

### Token Authentication

Include the token in the Authorization header:

```
Authorization: Token <your-token>
```

## Endpoints

### Uploads

#### List Uploads

```http
GET /api/uploads/
```

Response:
```json
[
    {
        "id": "uuid",
        "name": "string",
        "file": "string",
        "uploaded_at": "datetime",
        "owner": "uuid"
    }
]
```

#### Create Upload

```http
POST /api/uploads/
Content-Type: multipart/form-data

name: string
file: file
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "file": "string",
    "uploaded_at": "datetime",
    "owner": "uuid"
}
```

#### Get Upload

```http
GET /api/uploads/{id}/
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "file": "string",
    "uploaded_at": "datetime",
    "owner": "uuid"
}
```

#### Delete Upload

```http
DELETE /api/uploads/{id}/
```

Response: 204 No Content

### Snapshots

#### List Snapshots

```http
GET /api/snapshots/
```

Response:
```json
[
    {
        "id": "uuid",
        "name": "string",
        "dataset": "uuid",
        "created_at": "datetime",
        "owner": "uuid"
    }
]
```

#### Create Snapshot

```http
POST /api/snapshots/
Content-Type: application/json

{
    "name": "string",
    "dataset": "uuid"
}
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "dataset": "uuid",
    "created_at": "datetime",
    "owner": "uuid"
}
```

#### Get Snapshot

```http
GET /api/snapshots/{id}/
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "dataset": "uuid",
    "created_at": "datetime",
    "owner": "uuid"
}
```

#### Delete Snapshot

```http
DELETE /api/snapshots/{id}/
```

Response: 204 No Content

### Scenarios

#### List Scenarios

```http
GET /api/scenarios/
```

Response:
```json
[
    {
        "id": "uuid",
        "name": "string",
        "snapshot": "uuid",
        "param1": "float",
        "param2": "integer",
        "param3": "integer",
        "param4": "boolean",
        "param5": "boolean",
        "gpt_prompt": "string",
        "gpt_response": "string",
        "status": "string",
        "reason": "string",
        "created_at": "datetime",
        "updated_at": "datetime",
        "owner": "uuid"
    }
]
```

#### Create Scenario

```http
POST /api/scenarios/
Content-Type: application/json

{
    "name": "string",
    "snapshot": "uuid",
    "param1": "float",
    "param2": "integer",
    "param3": "integer",
    "param4": "boolean",
    "param5": "boolean",
    "gpt_prompt": "string"
}
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "snapshot": "uuid",
    "param1": "float",
    "param2": "integer",
    "param3": "integer",
    "param4": "boolean",
    "param5": "boolean",
    "gpt_prompt": "string",
    "gpt_response": "string",
    "status": "string",
    "reason": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "owner": "uuid"
}
```

#### Get Scenario

```http
GET /api/scenarios/{id}/
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "snapshot": "uuid",
    "param1": "float",
    "param2": "integer",
    "param3": "integer",
    "param4": "boolean",
    "param5": "boolean",
    "gpt_prompt": "string",
    "gpt_response": "string",
    "status": "string",
    "reason": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "owner": "uuid"
}
```

#### Delete Scenario

```http
DELETE /api/scenarios/{id}/
```

Response: 204 No Content

#### Add Constraint

```http
POST /api/scenarios/{id}/add_constraint/
Content-Type: application/json

{
    "prompt": "string"
}
```

Response:
```json
{
    "id": "uuid",
    "name": "string",
    "snapshot": "uuid",
    "param1": "float",
    "param2": "integer",
    "param3": "integer",
    "param4": "boolean",
    "param5": "boolean",
    "gpt_prompt": "string",
    "gpt_response": "string",
    "status": "string",
    "reason": "string",
    "created_at": "datetime",
    "updated_at": "datetime",
    "owner": "uuid"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request

```json
{
    "error": "string",
    "details": {}
}
```

### 401 Unauthorized

```json
{
    "error": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
    "error": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
    "error": "Not found."
}
```

### 500 Internal Server Error

```json
{
    "error": "An unexpected error occurred."
}
```

## Rate Limiting

API requests are limited to 100 requests per minute per IP address. The following headers are included in all responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed per minute
- `X-RateLimit-Remaining`: The number of requests remaining in the current rate limit window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets

## Pagination

List endpoints support pagination with the following query parameters:

- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 10, max: 100)

Response includes pagination metadata:

```json
{
    "count": "integer",
    "next": "string",
    "previous": "string",
    "results": []
}
```

## Filtering

List endpoints support filtering with query parameters:

### Uploads

- `name`: Filter by name (exact match)
- `owner`: Filter by owner ID
- `uploaded_at`: Filter by upload date (ISO format)

### Snapshots

- `name`: Filter by name (exact match)
- `dataset`: Filter by dataset ID
- `owner`: Filter by owner ID
- `created_at`: Filter by creation date (ISO format)

### Scenarios

- `name`: Filter by name (exact match)
- `snapshot`: Filter by snapshot ID
- `status`: Filter by status
- `owner`: Filter by owner ID
- `created_at`: Filter by creation date (ISO format)
- `updated_at`: Filter by update date (ISO format) 