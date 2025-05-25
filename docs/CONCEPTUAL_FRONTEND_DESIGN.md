# Conceptual Frontend Design: Video Analytics API

## 1. Introduction

*   **Purpose**: This document outlines a conceptual structure for a custom frontend application designed to interact with the Video Analytics Backend API. It serves as a high-level guide and starting point for frontend development.
*   **Scope**: This is not a detailed UI/UX design, wireframe document, or a complete technical specification. It focuses on the key views, components, and interaction patterns with the backend.
*   **Backend API Reference**: For all details regarding the backend API (endpoints, data models, authentication), please refer to the `COMPREHENSIVE_API_GUIDE.md`.

## 2. Core Principles

*   **Single Page Application (SPA)**: Recommended to provide a fluid and responsive user experience, minimizing full-page reloads.
*   **Component-Based Architecture**: Leveraging a modern JavaScript framework (such as React, Vue, or Angular) to build modular and reusable UI components.
*   **API-Driven**: All data display, manipulation, and control actions are mediated through the backend API. The frontend acts as a client to the backend.
*   **User-Friendly Interface**: The design should aim for clarity, ease of use, and intuitive navigation for managing complex configurations and tasks.

## 3. Key Views/Pages (Conceptual Examples)

This section describes potential views or pages within the frontend application.

### A. Dashboard/Overview

*   **Purpose**: To provide a quick, at-a-glance overview of the video analytics system's status and key metrics.
*   **Potential Content**:
    *   List of currently active camera processing tasks (names or IDs).
    *   Count of configured cameras, policies, and model settings.
    *   System health indicators (derived from the backend `/health` endpoint, showing API and database status).
    *   Quick links to management sections.
*   **API Interaction**:
    *   `GET /processing/status` (to list active tasks)
    *   `GET /configs/cameras`, `GET /configs/policies`, `GET /configs/model_settings` (for counts, potentially with query parameters for minimal data if just needing counts)
    *   `GET /health` (for system health indicators)

### B. Camera Configuration Management

*   **Purpose**: To allow users to perform CRUD (Create, Read, Update, Delete) operations on camera configurations.
*   **Layout**:
    *   A primary view displaying a table or list of all configured cameras, showing key information (e.g., name, URL, status, associated policy/model names).
    *   Actions (buttons/icons) for each camera: "Edit", "Delete", "Start/Stop Processing".
    *   An "Add Camera" button leading to a creation form.
    *   Modal dialogs or separate form views for creating and editing camera configurations.
*   **API Interaction**:
    *   `GET /configs/cameras` (to populate the list)
    *   `POST /configs/cameras` (for creating new cameras)
    *   `GET /configs/cameras/{id}` (to view/edit details of a specific camera)
    *   `PUT /configs/cameras/{id}` (to update a camera)
    *   `DELETE /configs/cameras/{id}` (to delete a camera)
*   **Considerations**:
    *   Forms for creating/editing cameras should include dropdowns or searchable selectors for `policy_id` and `model_settings_id`. These selectors would be populated by data fetched from `GET /configs/policies` and `GET /configs/model_settings` respectively.
    *   Displaying the names of the associated policy and model settings in the list view (requiring frontend-side mapping or backend API adjustments if direct names are needed in the camera list response).

### C. Policy Management

*   **Purpose**: To allow users to manage analysis policies.
*   **Layout**:
    *   Similar to Camera Configuration Management: a list/table view of existing policies.
    *   Actions for "Add Policy", "Edit", "Delete".
    *   Forms for creating/editing policies.
*   **API Interaction**:
    *   `GET /configs/policies`
    *   `POST /configs/policies`
    *   `GET /configs/policies/{id}`
    *   `PUT /configs/policies/{id}`
    *   `DELETE /configs/policies/{id}`
*   **Considerations**:
    *   The form for the `parameters` field (a flexible JSON object) might require a dynamic key-value editor, a raw JSON input field with validation, or UI elements that adapt based on the selected `policy_type` (if a predefined set of policy types with known parameters is established).

### D. Model Settings Management

*   **Purpose**: To allow users to manage AI model settings.
*   **Layout**:
    *   Similar to Camera and Policy Management: a list/table view, forms for creation/editing.
*   **API Interaction**:
    *   `GET /configs/model_settings`
    *   `POST /configs/model_settings`
    *   `GET /configs/model_settings/{id}`
    *   `PUT /configs/model_settings/{id}`
    *   `DELETE /configs/model_settings/{id}`

### E. Processing Control & Monitoring

*   **Purpose**: To enable users to start and stop video processing tasks for configured cameras and to view their real-time (or near real-time) status.
*   **Layout**:
    *   This functionality could be integrated directly into the "Camera Configuration Management" view (e.g., start/stop buttons and status indicators next to each camera in the list).
    *   Alternatively, a dedicated "Processing Dashboard" page could list all cameras and their processing status, with controls.
*   **API Interaction**:
    *   `POST /processing/start/{camera_id}`
    *   `POST /processing/stop/{camera_id}`
    *   `GET /processing/status/{camera_id}` (for individual status, potentially polled periodically)
    *   `GET /processing/status` (for an overview of all active tasks)
*   **Important Note**: The current backend API provides control and status information but **does not stream video or analysis results (e.g., bounding boxes, event logs)**. If live video display or visualization of analysis output is a future requirement, the backend API would need significant extensions (e.g., WebSocket support, endpoints for event streams or media). This conceptual frontend design assumes interaction with the current API capabilities.

### F. (Optional) System Settings/Administration

*   **Purpose**: For administrative tasks, potentially including frontend-specific settings or simplified backend configuration management.
*   **Potential Content**:
    *   **API Key Management (Frontend Context)**: If the frontend application is designed to be used by multiple individuals who might use a shared backend API key, or if each frontend user has their own backend API key, this section could allow users to input or update the `X-API-Key` value used by their browser/instance of the frontend. *This is distinct from managing API keys for the backend itself.*
    *   User management for the frontend application itself (if the frontend has its own login system, separate from the backend API key).
    *   Links to API documentation or health status.

## 4. Core Frontend Components (Conceptual)

A well-structured frontend would likely include the following types of components:

*   **API Client Service/Module**:
    *   A dedicated part of the frontend codebase (e.g., a JavaScript class or a set of functions) responsible for all HTTP communication with the backend API.
    *   This service would encapsulate logic for:
        *   Constructing API request URLs.
        *   Adding necessary headers, especially the `X-API-Key`.
        *   Sending requests (GET, POST, PUT, DELETE).
        *   Parsing JSON responses.
        *   Centralized error handling for API requests (e.g., network errors, 4xx/5xx status codes).
*   **State Management**:
    *   **Approach**: Depending on the chosen framework, this could be React Context API, Redux, Zustand (for React); Vuex, Pinia (for Vue); or services and RxJS (for Angular).
    *   **Purpose**: To manage application-wide state, such as:
        *   Lists of cameras, policies, and model settings fetched from the API.
        *   The current user's information or API key (if applicable to the frontend's auth model).
        *   Loading indicators for asynchronous operations.
        *   Error messages to be displayed to the user.
*   **Reusable UI Components**:
    *   **Forms**: Standardized form components for creating and editing Camera Configurations, Policies, and Model Settings, including input fields, dropdowns, validation logic, and submission handling.
    *   **Tables/Lists**: Components for displaying collections of items (cameras, policies, etc.) with features like sorting, pagination (if needed), and action buttons per row.
    *   **Modals/Dialogs**: For confirmations (e.g., "Are you sure you want to delete this item?"), displaying detailed information, or hosting forms.
    *   **Navigation**: Main navigation bar, sidebars, breadcrumbs for easy movement between views.
    *   **Status Indicators**: Visual cues for processing status (e.g., "Active", "Inactive", "Error").
    *   **Buttons**: Consistent styling for action buttons.
*   **Authentication Handling (Frontend Side)**:
    *   If the frontend is a simple admin interface used with a single, pre-shared backend API key, it might involve a configuration page or input field where the user can enter this key, which is then stored securely (e.g., in browser `localStorage` or `sessionStorage`, though `localStorage` has security implications if XSS is possible).
    *   If the frontend has its own user authentication system (separate from the backend's API key mechanism), that system would manage user logins. After a successful frontend login, the frontend might then retrieve or be configured with the appropriate `X-API-Key` to use for backend calls.

## 5. Example User Workflows

Illustrative workflows demonstrating how a user might interact with the frontend.

### Adding a New Camera

1.  **Navigation**: User navigates to the "Camera Configuration Management" view.
2.  **Initiate Action**: User clicks an "Add Camera" button.
3.  **Form Display**: Frontend displays a form for creating a new camera.
    *   Dropdowns for "Policy" and "Model Settings" are populated by data fetched via asynchronous calls to `GET /configs/policies` and `GET /configs/model_settings` by the API Client Service. The frontend might cache this data in its state.
4.  **User Input**: User fills in the camera name, URL, description, and selects a policy and model settings from the dropdowns.
5.  **Submission**: User clicks a "Save" or "Create" button.
6.  **API Request**: The frontend's API Client Service makes a `POST /configs/cameras` request to the backend, sending the form data (including the selected `policy_id` and `model_settings_id`) in the request body.
7.  **Feedback & Update**:
    *   On successful creation (e.g., 201 status from API), the frontend displays a success message.
    *   The list of cameras in the "Camera Configuration Management" view is refreshed (either by re-fetching the entire list via `GET /configs/cameras` or by intelligently updating the local state with the new camera data from the POST response).
    *   On failure (e.g., 422 validation error, 400 bad foreign key), the frontend displays an appropriate error message to the user, potentially highlighting specific fields in the form.

### Starting Video Processing for a Camera

1.  **Navigation**: User is in a view listing cameras (e.g., "Camera Configuration Management" or a dedicated "Processing Control" view).
2.  **Identify Camera**: User locates the specific camera for which they want to start processing. The camera's current processing status ("Active", "Inactive") might be displayed.
3.  **Initiate Action**: User clicks a "Start Processing" button associated with that camera.
4.  **API Request**: The frontend's API Client Service makes a `POST /processing/start/{camera_id}` request to the backend, using the ID of the selected camera.
5.  **Feedback & Update**:
    *   On success (200 status), the frontend displays a success message.
    *   The status indicator for that camera is updated to "Active". This might involve re-fetching the specific camera's status via `GET /processing/status/{camera_id}` or updating based on the successful start command.
    *   On failure (e.g., 400 if already active, 404 if camera not found), an error message is displayed.

## 6. Technology Stack Considerations (General Suggestions)

*   **JavaScript/TypeScript**: TypeScript is highly recommended for larger projects due to its static typing benefits, improving code quality and maintainability.
*   **Framework**:
    *   **React**: Large ecosystem, component-based, widely used. State management often handled by Context API, Redux, or Zustand.
    *   **Vue.js**: Known for its progressive framework nature and ease of integration. State management often handled by Pinia or Vuex.
    *   **Angular**: A comprehensive platform, good for large-scale applications, uses TypeScript by default.
    *   The choice depends on team familiarity, project requirements, and desired ecosystem.
*   **Styling**:
    *   **CSS Frameworks**: Tailwind CSS (utility-first), Bootstrap (component-based).
    *   **CSS-in-JS**: Styled-components, Emotion (if using React).
    *   Component-scoped CSS or CSS Modules.
*   **Build Tools**:
    *   **Vite**: Modern, fast build tool, offers excellent developer experience.
    *   **Webpack**: Mature, highly configurable, but can be more complex to set up.
*   **HTTP Client**: While native `fetch` can be used, libraries like `axios` are popular for features like request/response interception and easier error handling, often integrated into the API Client Service.

This conceptual design provides a foundational outline. Actual frontend development will involve detailed UI/UX design, component implementation, and thorough testing.
