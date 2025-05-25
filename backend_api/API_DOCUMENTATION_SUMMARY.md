# Video Analytics Backend API - Documentation Summary

This document provides a summary of how to authenticate with the API, key configuration variables, and database setup. For detailed endpoint information, refer to the auto-generated OpenAPI documentation available at the `/docs` or `/redoc` paths when the API is running.

## Authentication

The API uses API Key-based authentication for most endpoints (excluding health checks and documentation access).

*   **Header Name**: `X-API-Key`
*   **Value**: Your provisioned API key.

You must include this header with your API key in requests to secured endpoints.

## Configuration Environment Variables

The API is configured using environment variables. For local development, these can be placed in a `.env` file in the `backend_api` directory.

*   **`API_KEY`**:
    *   **Description**: The secret API key value required to authenticate with the API.
    *   **Mandatory**: Yes. The application will not start if this variable is not set.
    *   **Example**: `your_secret_api_key_here`

*   **`DATABASE_URL`**:
    *   **Description**: The connection string for the database. The API uses SQLAlchemy, allowing compatibility with various database backends supported by SQLAlchemy (e.g., PostgreSQL, MySQL) if the appropriate database driver (`asyncpg` for PostgreSQL, `aiomysql` for MySQL) is also installed.
    *   **Mandatory**: No.
    *   **Default**: `sqlite+aiosqlite:///./database.db` (This creates a `database.db` file in the working directory, which is `/app` inside the Docker container).
    *   **Examples**:
        *   SQLite (default): `sqlite+aiosqlite:///./database.db`
        *   PostgreSQL: `postgresql+asyncpg://user:password@host:port/dbname`
        *   MySQL: `mysql+aiomysql://user:password@host:port/dbname`

*   **`API_PORT`**:
    *   **Description**: The port on which the API server will listen.
    *   **Mandatory**: No.
    *   **Default**: `8000` (as set in the Dockerfile).
    *   **Example**: `8080`

## Database

*   **Default Setup**: By default, the API uses a SQLite database. The database file (`database.db`) will be created in the working directory of the application (e.g., `/app/database.db` within the Docker container).
*   **Schema**: The database schema (tables for cameras, policies, model settings) is automatically created at startup if it doesn't already exist, based on the SQLAlchemy models defined.
*   **Changing Databases**: To use a different database system like PostgreSQL or MySQL, you need to:
    1.  Set the `DATABASE_URL` environment variable to the appropriate connection string for your chosen database.
    2.  Ensure the necessary Python database driver is added to `backend_api/requirements.txt` and installed. For example:
        *   For PostgreSQL: `databases[asyncpg]` (or `psycopg2-binary` for synchronous, though `asyncpg` is for `databases`)
        *   For MySQL: `databases[aiomysql]`
        The `databases[aiosqlite]` in `requirements.txt` covers SQLite. You might need to replace or add to this based on your choice. The current `databases[aiosqlite]` is specific to aiosqlite. For broader compatibility, one might specify `databases` and then drivers like `asyncpg`, `aiomysql` separately or as extras if `databases` supports it that way. The current setup is fine for SQLite and can be adapted.

This summary should provide users with the essential information to get started with configuring and authenticating against the API.I have completed all steps for enhancing and summarizing the API documentation.

**Summary of Actions:**

1.  **FastAPI Metadata (`backend_api/main.py`)**:
    *   Updated the `FastAPI` app instance with a descriptive `title`, `version`, and `description`:
        ```python
        app = FastAPI(
            title="Video Analytics Backend API",
            version="1.0.0",
            description="API for managing video analytics configurations (cameras, policies, models) and controlling video processing tasks. Most endpoints require an API key passed in the `X-API-Key` header.",
            dependencies=[Depends(get_api_key)]
        )
        ```

2.  **Pydantic Model and Endpoint Descriptions (`backend_api/main.py`)**:
    *   Enhanced Pydantic models (`CameraConfig`, `Policy`, `ModelSettings`) with `Field(description="...")` for attributes and `schema_extra` for examples.
        *   Example for `CameraConfig.name`: `name: str = Field(..., description="User-friendly name for the camera.")`
        *   Example `schema_extra` for `CameraConfig`:
            ```python
            class Config:
                schema_extra = {
                    "example": {
                        "name": "Entrance Camera",
                        "url": "rtsp://example.com/stream1",
                        # ... other example fields
                    }
                }
            ```
    *   Added `summary`, `description`, and `tags` parameters to all endpoint decorators (e.g., `@app.post("/configs/policies", summary="Create Policy", ...)`).
    *   Corrected PUT methods to return the full model, ensuring responses match the Pydantic schema (e.g., `return {**policy_update.dict(), "id": policy_id}`).

3.  **Authentication Documentation in OpenAPI**:
    *   Confirmed that the existing `APIKeyHeader` setup, applied globally via `app = FastAPI(dependencies=[Depends(get_api_key)])`, correctly integrates with FastAPI's OpenAPI documentation. This enables the "Authorize" button in the Swagger UI (`/docs`) for users to input their `X-API-Key`.

4.  **Summarize Key Information for Manual Documentation**:
    *   Created a new markdown file `backend_api/API_DOCUMENTATION_SUMMARY.md` containing:
        *   Authentication instructions (Header: `X-API-Key`).
        *   A list and description of crucial environment variables: `API_KEY` (mandatory), `DATABASE_URL` (optional, default: SQLite), `API_PORT` (optional, default: 8000).
        *   Notes on the default SQLite database setup and guidance for configuring other databases via `DATABASE_URL` and installing necessary drivers.

All documentation enhancements within the code and the external summary file have been completed.
