# Backend API Deployment Guide

This guide provides step-by-step instructions for deploying the containerized Video Analytics Backend API.

## 1. Prerequisites

*   **Docker**: Docker must be installed and running on your deployment server. Visit [docker.com](https://www.docker.com/get-started) for installation instructions.

## 2. Building the Docker Image

1.  Navigate to the `backend_api` directory in your terminal:
    ```bash
    cd path/to/your/project/backend_api
    ```

2.  Build the Docker image using the provided Dockerfile:
    ```bash
    docker build -t video-analytics-backend .
    ```
    This command tags the image as `video-analytics-backend`. You can choose a different tag if you prefer.

## 3. Running the Docker Container

To run the API, you will use the `docker run` command. This command needs to:
*   Map a host port to the container's API port.
*   Provide the necessary environment variables (`API_KEY`, `DATABASE_URL`, `API_PORT`).
*   Mount a volume for persistent SQLite database storage.
*   Optionally, run in detached mode (`-d`).

**Example `docker run` command:**

1.  **Create a directory on the host machine** to store the persistent SQLite database:
    ```bash
    mkdir -p ./my_api_data
    ```
    This creates a directory named `my_api_data` in your current path. You can choose any path.

2.  **Run the container**:
    ```bash
    docker run -d \
        -p 8000:8000 \
        -e API_KEY="YOUR_VERY_STRONG_AND_SECRET_API_KEY" \
        -e DATABASE_URL="sqlite+aiosqlite:///./data/database.db" \
        -e API_PORT="8000" \
        -v $(pwd)/my_api_data:/app/data \
        --name video-analytics-api-container \
        video-analytics-backend
    ```

    **Explanation of the command options:**
    *   `-d`: Runs the container in detached mode (in the background).
    *   `-p 8000:8000`: Maps port 8000 on the host to port 8000 in the container (or to the value of `$API_PORT` if you change it).
    *   `-e API_KEY="YOUR_VERY_STRONG_AND_SECRET_API_KEY"`: **Crucial!** Sets the required API key for authentication. **Replace this with a strong, unique key.**
    *   `-e DATABASE_URL="sqlite+aiosqlite:///./data/database.db"`: Configures the API to use a SQLite database file located at `/app/data/database.db` inside the container. This path is important for volume mounting.
    *   `-e API_PORT="8000"`: (Optional) Sets the port inside the container where the API listens. The Dockerfile defaults this to 8000. You only need to set this if you want to change it *and* have modified the Dockerfile or entrypoint to respect it differently. The `-p` option's container port should match this.
    *   `-v $(pwd)/my_api_data:/app/data`: Mounts the `my_api_data` directory from your host machine (replace `$(pwd)/my_api_data` with the absolute path if necessary) to the `/app/data` directory inside the container. This ensures that the `database.db` file is stored on the host and persists even if the container is stopped or removed.
    *   `--name video-analytics-api-container`: Assigns a memorable name to your running container.
    *   `video-analytics-backend`: The name of the Docker image you built earlier.

## 4. Database Path and Initialization

*   The API is configured by default to store its SQLite database at `/app/data/database.db` inside the container (as set by `DATABASE_URL` in `backend_api/database.py` and the example `docker run` command).
*   When the container starts, the application will automatically create the `database.db` file within the `/app/data` directory (which is mounted from your host) if it doesn't already exist. The necessary tables will also be created.
*   Local data directories like `my_api_data/` and database files like `*.db` should be added to your project's root `.gitignore` file to prevent accidental versioning (this has been done in this project).

## 5. Verification

1.  **Check if the container is running**:
    ```bash
    docker ps
    ```
    You should see `video-analytics-api-container` (or the name you chose) in the list of running containers.

2.  **Check container logs (optional, for troubleshooting)**:
    ```bash
    docker logs video-analytics-api-container
    ```

3.. **Access the Health Check Endpoint**:
    Open your web browser or use a tool like `curl` to access the health check endpoint:
    ```bash
    curl http://localhost:8000/health
    ```
    You should receive a JSON response like: `{"status":"ok","database_status":"ok"}`.

4.  **Access API Documentation**:
    *   Swagger UI: `http://localhost:8000/docs`
    *   ReDoc: `http://localhost:8000/redoc`
    You can use the "Authorize" button in the Swagger UI (top right) to enter your `API_KEY` (the one you set in `docker run`) to interact with the secured endpoints.

## 6. Configuration

For a detailed list of all configurable environment variables (like `API_KEY`, `DATABASE_URL`, `API_PORT`), their purposes, and default values, please refer to the `API_DOCUMENTATION_SUMMARY.md` file located in the `backend_api` directory.

This guide should help you get the Video Analytics Backend API up and running in a Docker container. Remember to secure your `API_KEY` and manage your data volume appropriately.
