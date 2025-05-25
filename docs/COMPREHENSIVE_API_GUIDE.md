# Comprehensive API Guide: Video Analytics Backend

## 1. Introduction

The Video Analytics Backend API provides a robust interface for managing video analytics configurations, including camera setups, analysis policies, AI model settings, and controlling video processing tasks. It is designed to be a standalone, containerized service that your custom frontend or other services can interact with via HTTP requests.

For a fully interactive API specification, detailed model schemas, and the ability to try out endpoints, please refer to the auto-generated OpenAPI documentation available at the `/docs` endpoint (Swagger UI) or `/redoc` endpoint when the API service is running.

## 2. Authentication

The API secures most endpoints using an API Key.

*   **Method**: API Key passed in an HTTP header.
*   **Header Name**: `X-API-Key`
*   **Obtaining/Setting the Key**:
    *   The API key value is configured on the server-side using the `API_KEY` environment variable.
    *   Clients must include this exact key in the `X-API-Key` header with every request to secured endpoints.
    *   If the key is missing or incorrect, the API will respond with a `403 Forbidden` error (due to `auto_error=True` in the security scheme).

Publicly accessible endpoints (like `/health`, `/docs`, `/redoc`) do not require authentication.

## 3. Environment Variables for Configuration

The API's behavior is controlled by several environment variables:

*   **`API_KEY`**:
    *   **Description**: The secret API key value required to authenticate with the API. This is a critical security credential.
    *   **Mandatory**: Yes. The application will not start if this variable is not set.
    *   **Example**: `your_super_secret_api_key_12345`

*   **`DATABASE_URL`**:
    *   **Description**: The connection string for the database. The API uses SQLAlchemy and `databases`, allowing compatibility with various database backends.
    *   **Mandatory**: No.
    *   **Default**: `sqlite+aiosqlite:///./data/database.db` (This creates a `database.db` file within the `/app/data/` directory inside the Docker container, which is ideal for volume mounting).
    *   **Example Formats**:
        *   SQLite (default): `sqlite+aiosqlite:///./data/database.db`
        *   PostgreSQL: `postgresql+asyncpg://user:password@host:port/dbname`
        *   MySQL: `mysql+aiomysql://user:password@host:port/dbname` (Requires `aiomysql` driver)
    *   **Note**: Ensure the appropriate database driver (e.g., `asyncpg` for PostgreSQL) is installed if not using SQLite.

*   **`API_PORT`**:
    *   **Description**: The port on which the API server will listen inside the container.
    *   **Mandatory**: No.
    *   **Default**: `8000` (as set in the Dockerfile).
    *   **Example**: `8080`

For local development, these variables can be placed in a `.env` file in the `backend_api` directory.

## 4. API Endpoints Overview

This section provides a summary of the main API resources and their endpoints. For full request/response schemas and parameters, always refer to the OpenAPI documentation (`/docs`).

### 4.1 Health Check

*   **Endpoint**: `GET /health`
    *   **Purpose**: Checks the operational status of the API and its database connection. This endpoint is public and does not require authentication.
    *   **Key Request Parameters/Body Fields**: None.
    *   **Key Response Fields**:
        *   `status`: Overall API status (e.g., "ok").
        *   `database_status`: Status of the database connection (e.g., "ok" or "error").
    *   **Common Status Codes**:
        *   `200 OK`: API and database (if checked) are accessible.

### 4.2 Camera Configurations (`/configs/cameras`)

Manages video camera sources and their associated settings.

*   **Endpoint**: `POST /configs/cameras`
    *   **Purpose**: Creates a new camera configuration.
    *   **Key Request Body Fields**: `name` (str), `url` (str, e.g., RTSP link), `policy_id` (str, UUID), `model_settings_id` (str, UUID), `description` (Optional[str]), `is_active` (bool, default: True).
    *   **Key Response Fields**: The created camera configuration object, including its auto-generated `id` (str, UUID).
    *   **Common Status Codes**: `201 Created`, `400 Bad Request` (e.g., if `policy_id` or `model_settings_id` not found), `403 Forbidden` (auth error), `422 Unprocessable Entity` (validation error).

*   **Endpoint**: `GET /configs/cameras`
    *   **Purpose**: Retrieves a list of all camera configurations.
    *   **Key Response Fields**: A list of camera configuration objects.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`.

*   **Endpoint**: `GET /configs/cameras/{camera_id}`
    *   **Purpose**: Retrieves a specific camera configuration by its ID.
    *   **Key Response Fields**: The camera configuration object.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`.

*   **Endpoint**: `PUT /configs/cameras/{camera_id}`
    *   **Purpose**: Updates an existing camera configuration.
    *   **Key Request Body Fields**: Same as POST; all fields required by the model must be sent for a valid update.
    *   **Key Response Fields**: The updated camera configuration object.
    *   **Common Status Codes**: `200 OK`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`.

*   **Endpoint**: `DELETE /configs/cameras/{camera_id}`
    *   **Purpose**: Deletes a camera configuration.
    *   **Key Response Fields**: Success message.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`.

### 4.3 Policies (`/configs/policies`)

Manages analysis policies that define rules or parameters for video processing.

*   **Endpoint**: `POST /configs/policies`
    *   **Purpose**: Creates a new policy.
    *   **Key Request Body Fields**: `name` (str), `policy_type` (str), `parameters` (Dict[str, Any]).
    *   **Key Response Fields**: The created policy object, including its auto-generated `id` (str, UUID).
    *   **Common Status Codes**: `201 Created`, `403 Forbidden`, `422 Unprocessable Entity`.

*   **Endpoint**: `GET /configs/policies`
    *   **Purpose**: Retrieves a list of all policies.
    *   **Key Response Fields**: A list of policy objects.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`.

*   **Endpoint**: `GET /configs/policies/{policy_id}`
    *   **Purpose**: Retrieves a specific policy by its ID.
    *   **Key Response Fields**: The policy object.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`.

*   **Endpoint**: `PUT /configs/policies/{policy_id}`
    *   **Purpose**: Updates an existing policy.
    *   **Key Request Body Fields**: Same as POST.
    *   **Key Response Fields**: The updated policy object.
    *   **Common Status Codes**: `200 OK`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`.

*   **Endpoint**: `DELETE /configs/policies/{policy_id}`
    *   **Purpose**: Deletes a policy. (Note: Currently allows deletion even if in use by a CameraConfig).
    *   **Key Response Fields**: Success message.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`.

### 4.4 Model Settings (`/configs/model_settings`)

Manages configurations for AI models, including paths and operational parameters.

*   **Endpoint**: `POST /configs/model_settings`
    *   **Purpose**: Creates new model settings.
    *   **Key Request Body Fields**: `name` (str), `model_path` (str), `confidence_threshold` (float), `iou_threshold` (float), `other_params` (Optional[Dict[str, Any]]).
    *   **Key Response Fields**: The created model settings object, including its auto-generated `id` (str, UUID).
    *   **Common Status Codes**: `201 Created`, `403 Forbidden`, `422 Unprocessable Entity`.

*   **Endpoint**: `GET /configs/model_settings`
    *   **Purpose**: Retrieves a list of all model settings.
    *   **Key Response Fields**: A list of model settings objects.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`.

*   **Endpoint**: `GET /configs/model_settings/{model_settings_id}`
    *   **Purpose**: Retrieves specific model settings by ID.
    *   **Key Response Fields**: The model settings object.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`.

*   **Endpoint**: `PUT /configs/model_settings/{model_settings_id}`
    *   **Purpose**: Updates existing model settings.
    *   **Key Request Body Fields**: Same as POST.
    *   **Key Response Fields**: The updated model settings object.
    *   **Common Status Codes**: `200 OK`, `400 Bad Request`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity`.

*   **Endpoint**: `DELETE /configs/model_settings/{model_settings_id}`
    *   **Purpose**: Deletes model settings. (Note: Currently allows deletion even if in use by a CameraConfig).
    *   **Key Response Fields**: Success message.
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found`.

### 4.5 Video Processing Control (`/processing`)

Endpoints to control and query the status of video processing tasks. These tasks are currently managed in-memory.

*   **Endpoint**: `POST /processing/start/{camera_config_id}`
    *   **Purpose**: Starts the video processing task for a specified camera configuration ID.
    *   **Key Response Fields**: Message confirming start and `camera_config_id`.
    *   **Common Status Codes**: `200 OK`, `400 Bad Request` (e.g., already active), `403 Forbidden`, `404 Not Found` (camera config not found).

*   **Endpoint**: `POST /processing/stop/{camera_config_id}`
    *   **Purpose**: Stops an active video processing task for a camera configuration ID.
    *   **Key Response Fields**: Message confirming stop and `camera_config_id`.
    *   **Common Status Codes**: `200 OK`, `400 Bad Request` (e.g., not active), `403 Forbidden`.

*   **Endpoint**: `GET /processing/status`
    *   **Purpose**: Retrieves a list of all camera configuration IDs for which processing tasks are currently active.
    *   **Key Response Fields**: `active_tasks` (List[str]).
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`.

*   **Endpoint**: `GET /processing/status/{camera_config_id}`
    *   **Purpose**: Retrieves the processing status ('active' or 'inactive') for a specific camera configuration ID.
    *   **Key Response Fields**: `camera_config_id` (str), `status` (str).
    *   **Common Status Codes**: `200 OK`, `403 Forbidden`, `404 Not Found` (camera config not found).

## 5. Key Data Models (Conceptual Overview)

The API revolves around a few core data entities. For detailed schemas (fields, data types, optionality), please consult the OpenAPI documentation (`/docs`).

*   **CameraConfig**:
    *   Represents a physical or virtual video camera.
    *   Attributes include its name, stream URL, description, an active status flag, and references (`policy_id`, `model_settings_id`) to the policy and model settings it should use.

*   **Policy**:
    *   Defines a set of rules or parameters for a specific type of video analysis (e.g., intrusion detection, loitering detection).
    *   Attributes include a name, a policy type identifier, and a flexible `parameters` dictionary to hold type-specific settings.

*   **ModelSettings**:
    *   Specifies an AI model to be used for analysis and its operational parameters.
    *   Attributes include a name, the path to the model file, confidence and IOU thresholds for detections, and an optional `other_params` dictionary for additional model-specific configurations.

## 6. Error Handling

*   The API uses standard HTTP status codes to indicate the success or failure of requests.
*   For client errors (4xx range), the response body is typically JSON and includes a `detail` field providing more specific information about the error.
    *   `400 Bad Request`: Often used if a foreign key (like `policy_id`) in a request does not exist, or if there's an ID mismatch in PUT requests.
    *   `403 Forbidden`: Authentication failure (missing or invalid `X-API-Key`).
    *   `404 Not Found`: The requested resource (e.g., a specific camera) does not exist.
    *   `422 Unprocessable Entity`: The request body fails Pydantic model validation (e.g., missing required fields, incorrect data types).

## 7. Frontend Integration Notes

This section provides guidance for integrating a custom frontend with this backend API.

*   **Separation of Concerns**: The backend API is a standalone service. Any frontend (web, mobile, etc.) is a separate application that communicates with this API. The Streamlit files in the original repository are not part of this containerized backend.
*   **API Interaction**:
    *   Your custom frontend will interact with the backend API via standard HTTP requests to the endpoints defined above (and detailed in `/docs`).
    *   All data management (CRUD operations for cameras, policies, model settings) and video processing control (start, stop, status) are handled through these API endpoints.
*   **Authentication**: For secured endpoints, the frontend must include the `X-API-Key` header with the valid API key.
*   **Deployment**: The custom frontend will have its own deployment strategy. It must be configured to send API requests to the URL where the backend API container is deployed (e.g., `http://<your-backend-api-host>:<API_PORT>`).
*   **Data Flow**: The backend API is the single source of truth. The frontend should rely on it for all data and control operations.

This guide provides a comprehensive starting point for understanding and integrating with the Video Analytics Backend API. Always refer to the interactive OpenAPI documentation (`/docs`) for the most detailed and up-to-date specifications.
