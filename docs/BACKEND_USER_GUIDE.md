# Backend API User Guide

## 1. Introduction

*   **Purpose**: This guide is designed to help end-users and administrators manage the Video Analytics system effectively through its Application Programming Interface (API). It covers common operations for managing configurations and controlling video processing tasks.
*   **Prerequisites**:
    *   The Video Analytics Backend API is deployed and accessible via a network URL.
    *   You have a valid `X-API-Key` for authentication.
*   **Tools for API Interaction**: You can interact with the API using various HTTP client tools, such as:
    *   `curl`: A command-line tool for making HTTP requests (examples provided in this guide).
    *   Postman: A graphical application for API testing and development.
    *   Custom scripts or applications written in programming languages like Python (using libraries such as `requests` or `httpx`), JavaScript, etc.
*   **Further Reference**: For detailed endpoint specifications, request/response schemas, and interactive testing, please consult the `COMPREHENSIVE_API_GUIDE.md` and the live OpenAPI documentation available at the `/docs` (Swagger UI) or `/redoc` endpoints of your deployed API instance.

## 2. Core Concepts (Brief Recap)

The API revolves around these central ideas:

*   **Camera Configurations**: These represent individual video sources (e.g., RTSP streams from IP cameras) and link them to specific analysis policies and AI model settings.
*   **Policies**: These define the "what" and "how" of video analysis. A policy might specify a type of detection (e.g., "intrusion_detection") and include parameters like sensitivity levels or detection zones.
*   **Model Settings**: These control the parameters of the AI models used for analysis, such as the path to the model file, confidence thresholds for detections, and IOU (Intersection over Union) thresholds.
*   **Processing Tasks**: These are the actual instances of video analysis running for a specific camera configuration. The API allows you to start, stop, and check the status of these tasks.

## 3. Managing Camera Configurations

These endpoints allow you to manage the video sources connected to the system. Remember to replace `<your_api_host>:<port>` with the actual URL of your API deployment and `<your_api_key>` with your valid API key.

### Listing Cameras

*   **Endpoint**: `GET /configs/cameras`
*   **Purpose**: Retrieves a list of all configured cameras.
*   **Example**:
    ```bash
    curl -X GET "http://<your_api_host>:<port>/configs/cameras" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON array of camera configuration objects.

### Creating a Camera

*   **Endpoint**: `POST /configs/cameras`
*   **Purpose**: Adds a new camera configuration to the system.
*   **Required Data**:
    *   `name` (string): A user-friendly name for the camera.
    *   `url` (string): The video stream URL (e.g., `rtsp://user:pass@ip_address/stream_path`).
    *   `policy_id` (string): The ID of an existing Policy to apply to this camera.
    *   `model_settings_id` (string): The ID of an existing Model Settings configuration to use.
    *   You may also include `description` (string, optional) and `is_active` (boolean, optional, defaults to `true`).
*   **Note**: You must first create or identify valid `policy_id` and `model_settings_id` values by listing or creating those resources (see sections 4 and 5).
*   **Example**:
    ```bash
    curl -X POST "http://<your_api_host>:<port>/configs/cameras" \
         -H "X-API-Key: <your_api_key>" \
         -H "Content-Type: application/json" \
         -d '{
               "name": "Front Door Camera",
               "url": "rtsp://admin:password123@192.168.1.100/stream1",
               "description": "Primary entrance monitoring",
               "policy_id": "existing_policy_uuid_here",
               "model_settings_id": "existing_model_settings_uuid_here",
               "is_active": true
             }'
    ```
*   **Expected Output**: A JSON object of the newly created camera configuration, including its system-generated `id`.

### Viewing a Specific Camera

*   **Endpoint**: `GET /configs/cameras/{camera_id}`
*   **Purpose**: Retrieves details for a single camera configuration.
*   **Example**: Replace `{camera_id}` with the actual ID.
    ```bash
    curl -X GET "http://<your_api_host>:<port>/configs/cameras/your_camera_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON object of the camera configuration.

### Updating a Camera

*   **Endpoint**: `PUT /configs/cameras/{camera_id}`
*   **Purpose**: Modifies an existing camera configuration.
*   **Note**: The request body should contain all fields for the camera, even those not being changed, as per standard PUT behavior for this API.
*   **Example**: Replace `{camera_id}` with the actual ID.
    ```bash
    curl -X PUT "http://<your_api_host>:<port>/configs/cameras/your_camera_id_here" \
         -H "X-API-Key: <your_api_key>" \
         -H "Content-Type: application/json" \
         -d '{
               "name": "Front Door Camera (Updated)",
               "url": "rtsp://admin:newpass@192.168.1.100/stream1",
               "description": "Primary entrance monitoring - new description",
               "policy_id": "updated_policy_uuid_here",
               "model_settings_id": "existing_model_settings_uuid_here",
               "is_active": false
             }'
    ```
*   **Expected Output**: A JSON object of the updated camera configuration.

### Deleting a Camera

*   **Endpoint**: `DELETE /configs/cameras/{camera_id}`
*   **Purpose**: Removes a camera configuration from the system.
*   **Example**: Replace `{camera_id}` with the actual ID.
    ```bash
    curl -X DELETE "http://<your_api_host>:<port>/configs/cameras/your_camera_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON object with a success message, e.g., `{"message": "Camera deleted successfully"}`.

## 4. Managing Policies

Policies define the rules and parameters for video analysis.

### Listing Policies

*   **Endpoint**: `GET /configs/policies`
*   **Example**:
    ```bash
    curl -X GET "http://<your_api_host>:<port>/configs/policies" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON array of policy objects.

### Creating a Policy

*   **Endpoint**: `POST /configs/policies`
*   **Required Data**:
    *   `name` (string): A user-friendly name for the policy.
    *   `policy_type` (string): Identifier for the type of policy (e.g., "intrusion_detection", "loitering_alert").
    *   `parameters` (object/dictionary): A flexible JSON object containing key-value pairs specific to the `policy_type`.
*   **Example**:
    ```bash
    curl -X POST "http://<your_api_host>:<port>/configs/policies" \
         -H "X-API-Key: <your_api_key>" \
         -H "Content-Type: application/json" \
         -d '{
               "name": "High Sensitivity Intrusion Zone",
               "policy_type": "intrusion_detection",
               "parameters": {
                 "sensitivity": "high",
                 "detection_area_polygon": [
                   {"x": 0, "y": 0},
                   {"x": 1280, "y": 0},
                   {"x": 1280, "y": 720},
                   {"x": 0, "y": 720}
                 ],
                 "min_object_size": 50
               }
             }'
    ```
*   **Expected Output**: A JSON object of the newly created policy, including its system-generated `id`.

### Viewing a Specific Policy

*   **Endpoint**: `GET /configs/policies/{policy_id}`
*   **Example**: Replace `{policy_id}` with the actual ID.
    ```bash
    curl -X GET "http://<your_api_host>:<port>/configs/policies/your_policy_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON object of the policy.

### Updating a Policy

*   **Endpoint**: `PUT /configs/policies/{policy_id}`
*   **Note**: The request body should contain all fields for the policy.
*   **Example**: Replace `{policy_id}` with the actual ID.
    ```bash
    curl -X PUT "http://<your_api_host>:<port>/configs/policies/your_policy_id_here" \
         -H "X-API-Key: <your_api_key>" \
         -H "Content-Type: application/json" \
         -d '{
               "name": "High Sensitivity Intrusion Zone (Revised)",
               "policy_type": "intrusion_detection_v2",
               "parameters": {
                 "sensitivity": "medium",
                 "detection_area_polygon": [{"x": 10,"y": 10},{"x": 100,"y": 10},{"x": 100,"y": 100},{"x": 10,"y": 100}],
                 "min_object_size": 60,
                 "alert_cooldown_seconds": 30
               }
             }'
    ```
*   **Expected Output**: A JSON object of the updated policy.

### Deleting a Policy

*   **Endpoint**: `DELETE /configs/policies/{policy_id}`
*   **Note**: The API currently allows deleting a policy even if it's associated with a CameraConfig. This might lead to orphaned references.
*   **Example**: Replace `{policy_id}` with the actual ID.
    ```bash
    curl -X DELETE "http://<your_api_host>:<port>/configs/policies/your_policy_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: `{"message": "Policy deleted successfully"}`.

## 5. Managing Model Settings

Model settings define which AI model to use and its operational parameters.

### Listing Model Settings

*   **Endpoint**: `GET /configs/model_settings`
*   **Example**:
    ```bash
    curl -X GET "http://<your_api_host>:<port>/configs/model_settings" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON array of model settings objects.

### Creating Model Settings

*   **Endpoint**: `POST /configs/model_settings`
*   **Required Data**:
    *   `name` (string): A user-friendly name.
    *   `model_path` (string): Path to the model file (e.g., `/models/yolov8m.pt`).
    *   `confidence_threshold` (float): Detection confidence threshold (e.g., 0.5).
    *   `iou_threshold` (float): Intersection over Union threshold (e.g., 0.45).
    *   `other_params` (object/dictionary, optional): Additional model-specific parameters.
*   **Example**:
    ```bash
    curl -X POST "http://<your_api_host>:<port>/configs/model_settings" \
         -H "X-API-Key: <your_api_key>" \
         -H "Content-Type: application/json" \
         -d '{
               "name": "YOLOv8 Medium - General Purpose",
               "model_path": "/opt/models/yolov8m.pt",
               "confidence_threshold": 0.55,
               "iou_threshold": 0.5,
               "other_params": {
                 "img_size": 640,
                 "device": "cpu"
               }
             }'
    ```
*   **Expected Output**: A JSON object of the newly created model settings, including its system-generated `id`.

### Viewing Specific Model Settings

*   **Endpoint**: `GET /configs/model_settings/{model_settings_id}`
*   **Example**: Replace `{model_settings_id}` with the actual ID.
    ```bash
    curl -X GET "http://<your_api_host>:<port>/configs/model_settings/your_model_settings_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON object of the model settings.

### Updating Model Settings

*   **Endpoint**: `PUT /configs/model_settings/{model_settings_id}`
*   **Note**: The request body should contain all fields for the model settings.
*   **Example**: Replace `{model_settings_id}` with the actual ID.
    ```bash
    curl -X PUT "http://<your_api_host>:<port>/configs/model_settings/your_model_settings_id_here" \
         -H "X-API-Key: <your_api_key>" \
         -H "Content-Type: application/json" \
         -d '{
               "name": "YOLOv8 Medium - GPU Optimized",
               "model_path": "/opt/models/yolov8m_gpu.pt",
               "confidence_threshold": 0.6,
               "iou_threshold": 0.45,
               "other_params": {
                 "img_size": 640,
                 "device": "cuda:0"
               }
             }'
    ```
*   **Expected Output**: A JSON object of the updated model settings.

### Deleting Model Settings

*   **Endpoint**: `DELETE /configs/model_settings/{model_settings_id}`
*   **Note**: The API currently allows deleting model settings even if associated with a CameraConfig.
*   **Example**: Replace `{model_settings_id}` with the actual ID.
    ```bash
    curl -X DELETE "http://<your_api_host>:<port>/configs/model_settings/your_model_settings_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: `{"message": "ModelSettings deleted successfully"}`.

## 6. Controlling Video Processing

These endpoints manage the lifecycle of video analysis tasks. Processing tasks are currently managed in-memory by the API instance.

### Starting a Processing Task

*   **Endpoint**: `POST /processing/start/{camera_config_id}`
*   **Purpose**: Initiates video analysis for the camera specified by `camera_config_id`.
*   **Note**: A valid Camera Configuration with the given ID must exist.
*   **Example**: Replace `{camera_config_id}` with the actual ID.
    ```bash
    curl -X POST "http://<your_api_host>:<port>/processing/start/your_camera_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: `{"message": "Processing started", "camera_config_id": "your_camera_id_here"}`.

### Stopping a Processing Task

*   **Endpoint**: `POST /processing/stop/{camera_config_id}`
*   **Purpose**: Stops an active video analysis task for the given `camera_config_id`.
*   **Example**: Replace `{camera_config_id}` with the actual ID.
    ```bash
    curl -X POST "http://<your_api_host>:<port>/processing/stop/your_camera_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: `{"message": "Processing stopped", "camera_config_id": "your_camera_id_here"}`.

### Checking Overall Status

*   **Endpoint**: `GET /processing/status`
*   **Purpose**: Lists the IDs of all camera configurations for which processing tasks are currently active.
*   **Example**:
    ```bash
    curl -X GET "http://<your_api_host>:<port>/processing/status" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: A JSON object like `{"active_tasks": ["camera_id_1", "camera_id_2"]}`.

### Checking Status of a Specific Camera

*   **Endpoint**: `GET /processing/status/{camera_config_id}`
*   **Purpose**: Checks if processing is 'active' or 'inactive' for a specific camera.
*   **Example**: Replace `{camera_config_id}` with the actual ID.
    ```bash
    curl -X GET "http://<your_api_host>:<port>/processing/status/your_camera_id_here" \
         -H "X-API-Key: <your_api_key>"
    ```
*   **Expected Output**: `{"camera_config_id": "your_camera_id_here", "status": "active"}` or `{"camera_config_id": "your_camera_id_here", "status": "inactive"}`.

## 7. Troubleshooting Common Issues (Briefly)

*   **Authentication Errors (`403 Forbidden`)**:
    *   Ensure the `X-API-Key` header is included in your request.
    *   Verify that the API key value is correct and matches the `API_KEY` environment variable set on the server.
*   **Not Found Errors (`404 Not Found`)**:
    *   Double-check that the ID you are using in the URL path (e.g., for a specific camera, policy, or model setting) is correct and exists in the system.
    *   When creating a camera, ensure the `policy_id` and `model_settings_id` you provide in the request body already exist.
*   **Invalid Input (`422 Unprocessable Entity` or `400 Bad Request`)**:
    *   **422**: Usually indicates that the request body failed Pydantic validation. Check that all required fields are present and that data types are correct (e.g., string, integer, boolean, dictionary where expected). Refer to the API's `/docs` for exact model schemas.
    *   **400**: Can indicate issues like trying to create a Camera with a `policy_id` or `model_settings_id` that doesn't exist, or an ID mismatch in a PUT request. The `detail` field in the JSON response will provide more specific information.

This guide should provide a solid foundation for interacting with the Video Analytics Backend API. For any ambiguities or more complex scenarios, consult the detailed OpenAPI documentation.Okay, I've created the `BACKEND_USER_GUIDE.md` in the root directory with the structure and content as requested.

It includes:
1.  **Introduction**: Purpose, prerequisites, tools for API interaction, and a reference to the comprehensive guide.
2.  **Core Concepts**: Brief recap of Camera Configurations, Policies, Model Settings, and Processing Tasks.
3.  **Managing Camera Configurations**: Detailed examples for listing, creating, viewing, updating, and deleting camera configurations using `curl`.
4.  **Managing Policies**: Similar detailed examples for CRUD operations on policies.
5.  **Managing Model Settings**: Similar detailed examples for CRUD operations on model settings.
6.  **Controlling Video Processing**: Examples for starting, stopping, and checking the status of video processing tasks.
7.  **Troubleshooting Common Issues**: Brief guidance on handling 401/403, 404, and 422/400 errors.

The `curl` examples use placeholders like `<your_api_host>:<port>` and `<your_api_key>` consistently. The tone is instructional, aimed at enabling a user to manage the system via the API.
