# Frontend Integration Notes

This document provides guidance and considerations for integrating your custom frontend with the newly developed containerized backend API.

## 1. Separation of Frontend and Backend

*   The recent modifications have focused on creating a **standalone, containerized backend API**. This API is responsible for data management, business logic, and video processing control.
*   The existing Streamlit application files in this repository (e.g., `dashboard.py`, `safety_app.py`, `securade.py`, files in `pages/`) represent the original Python-based web application, which previously served as the frontend and backend.
*   This original Streamlit frontend is **not directly part of the containerized backend API deployment**. The backend API now operates independently.

## 2. Interaction with the Backend API

*   Your new custom frontend (e.g., a web application using React, Vue, Angular, a mobile application, or any other client) will interact with the backend API via standard **HTTP requests**.
*   For comprehensive details on available API endpoints, request/response formats, Pydantic models, and authentication, please refer to:
    *   The API documentation summary: `backend_api/API_DOCUMENTATION_SUMMARY.md`
    *   The auto-generated OpenAPI (Swagger) documentation available at the `/docs` endpoint of the running backend API.
    *   The auto-generated ReDoc documentation available at the `/redoc` endpoint of the running backend API.
*   Remember that most API endpoints are secured and require an `X-API-Key` header for authentication, as detailed in the documentation.

## 3. Deployment Considerations for Frontend

*   Your custom frontend will require its **own deployment strategy**, separate from the backend API Docker container.
*   The frontend application must be configured to send API requests to the **URL where the backend API is deployed** (e.g., `http://<your-backend-api-host>:<port>`). This URL will depend on your backend API's deployment environment.

## 4. Data Flow

*   All application data, including camera configurations, policies, and model settings, is now managed exclusively **via the backend API**.
*   Your frontend will use the defined API endpoints to perform CRUD (Create, Read, Update, Delete) operations on this data.
*   Similarly, control over video processing tasks (start, stop, status) is also handled through the API.

## 5. Original Streamlit App (Optional Usage)

*   You can still run the original Streamlit application from this repository if desired (e.g., for UI reference, to understand previous workflows, or if parts of its logic are useful for your new frontend).
*   However, it would typically operate **independently** of the new containerized backend API. It would require its own Python environment setup as per the original project's instructions.
*   Crucially, the original Streamlit application, unless significantly modified, would **not** inherently use the new SQLite database managed by the API, nor would it use the API key authentication mechanism. It would function based on its original data handling and configuration methods.

These notes should help clarify how your custom frontend interacts with the provided backend API. Focus on using the API as the single source of truth and interaction point for all data and processing control.
