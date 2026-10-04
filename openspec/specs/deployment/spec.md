# Spec: deployment

## Purpose
Define cloud deployment parameters, dynamic port binding, readiness health checks, and environment variable isolation.

## Requirements

### Requirement: Dynamic port binding
The application SHALL read the environment variable `$PORT` and bind uvicorn server to `0.0.0.0:$PORT`.

#### Scenario: Production start command
- GIVEN the service is launched on Render with environment variable PORT set
- WHEN uvicorn starts `app:app`
- THEN the web server listens on the specified PORT

### Requirement: Health check endpoint
The system SHALL expose `GET /healthz` returning HTTP 200 `{"status": "ok"}` without calling external services.

#### Scenario: Readiness check query
- GIVEN the application is running
- WHEN a GET request is sent to `/healthz`
- THEN HTTP status 200 with `{"status": "ok"}` is returned immediately

### Requirement: Environment secret isolation
Secrets like `GEMINI_API_KEY` and `DATABASE_URL` MUST NOT be tracked in Git version control files.

#### Scenario: Git tracking audit
- GIVEN the project repository files
- WHEN checking tracked files via git
- THEN `.env` file is excluded by `.gitignore`
