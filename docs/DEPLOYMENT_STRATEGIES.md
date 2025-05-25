# Deployment Strategies: Video Analytics Backend API

## 1. Introduction

This document provides detailed strategies and guidance for deploying the containerized Video Analytics Backend API in various environments. It expands upon the basic deployment steps and considers different operational scenarios.

For specific API endpoint details, data models, and authentication mechanisms, please refer to the [Comprehensive API Guide](./COMPREHENSIVE_API_GUIDE.md). The Docker configuration can be found in [../backend_api/Dockerfile](../backend_api/Dockerfile).

## 2. Core Deployment Method: Docker Container

The primary method for deploying the backend API is via the provided Docker container. This ensures consistency across different environments.

### 2.1. Building the Docker Image

1.  Navigate to the `backend_api` directory in your terminal:
    ```bash
    cd path/to/your/project/backend_api
    ```
    (If you are in the root of the repository, this would be `cd backend_api`)

2.  Build the Docker image:
    ```bash
    docker build -t video-analytics-backend .
    ```
    This command tags the image as `video-analytics-backend`. You can choose a different tag, such as `your-repo/video-analytics-backend:latest`.

### 2.2. Running the Docker Container (General Example)

The following `docker run` command illustrates a general deployment, which can be adapted based on the specific environment:

```bash
docker run -d \
    -p <host_port>:${API_PORT:-8000} \
    -e API_KEY="YOUR_VERY_STRONG_AND_SECRET_API_KEY" \
    -e DATABASE_URL="<your_database_url>" \
    -e API_PORT="<port_inside_container>" \
    -v <path_on_host_for_data>:/app/data \
    --name video-analytics-app \
    video-analytics-backend
```

**Explanation of `docker run` options:**

*   `-d`: Runs the container in detached mode (in the background).
*   `-p <host_port>:${API_PORT:-8000}`: Maps `<host_port>` on the host to the port the API listens on inside the container. The `${API_PORT:-8000}` syntax uses the value of the `API_PORT` environment variable if set, otherwise defaults to `8000`.
*   `-e API_KEY="YOUR_VERY_STRONG_AND_SECRET_API_KEY"`: **Crucial!** Sets the required API key for authentication. This must be a strong, unique key.
*   `-e DATABASE_URL="<your_database_url>"`: Configures the database connection string.
    *   For SQLite (default): `"sqlite+aiosqlite:///./data/database.db"` (Path is relative to `/app` inside the container).
    *   For PostgreSQL: `"postgresql+asyncpg://user:password@host:port/dbname"`
    *   For MySQL: `"mysql+aiomysql://user:password@host:port/dbname"`
*   `-e API_PORT="<port_inside_container>"`: (Optional) Sets the port on which the Uvicorn server listens inside the container. The Dockerfile's `CMD` uses this variable, defaulting to `8000`. Ensure this matches the container port in the `-p` mapping.
*   `-v <path_on_host_for_data>:/app/data`: Mounts a directory from the host machine to `/app/data` inside the container. This is essential for persisting SQLite database files. For other databases like PostgreSQL/MySQL hosted externally, this volume mount for `/app/data` may not be needed for the API container itself unless other local data storage is used by the application.
*   `--name video-analytics-app`: Assigns a memorable name to your running container.
*   `video-analytics-backend`: The name (and optionally tag) of the Docker image you built.

## 3. Deployment Environments

### A. Local Server / On-Premise

*   **Method**: Direct Docker deployment on a physical or virtual server within your infrastructure.
*   **Database**:
    *   **SQLite**:
        *   Use the volume mount as shown in the example (`-v /path/to/your/host/data:/app/data`).
        *   **Pros**: Simple setup, self-contained.
        *   **Cons**: Single-file database, potential performance bottlenecks under high concurrent load, backup requires manual file copying or snapshotting of the volume. Not suitable for multi-container scaling of the API.
    *   **Self-hosted PostgreSQL/MySQL**:
        *   Set up a dedicated PostgreSQL or MySQL server.
        *   Configure `DATABASE_URL` to point to this server (e.g., `postgresql+asyncpg://user:pass@your_db_host:5432/videodb`).
        *   **Pros**: More robust, scalable, supports concurrent connections better, mature backup/restore tools.
        *   **Cons**: Requires separate database server setup, maintenance, and administration.
*   **Networking**:
    *   Expose the container's API port to the host server using the `-p` option.
    *   Manage access to the host server and port via firewalls (e.g., UFW, iptables, or cloud provider security groups if in a VPC).
    *   Consider using a reverse proxy (e.g., Nginx, Caddy, Traefik) in front of the Docker container to handle HTTPS termination, load balancing (if scaling), rate limiting, and easier domain name management.
*   **Maintenance**:
    *   Updates involve pulling the new Docker image, stopping and removing the old container, and running a new container with the updated image and the same configurations (especially volume mounts and environment variables).
    *   **Docker Compose**: For easier management of the API container (and potentially a local database container for development/testing), consider using Docker Compose. A `docker-compose.yml` file can define the service, environment variables, volumes, and ports.
        ```yaml
        # Example docker-compose.yml snippet
        version: '3.8'
        services:
          video-analytics-api:
            image: video-analytics-backend # Or your custom image tag
            container_name: video-analytics-app
            ports:
              - "8000:8000" # <host_port>:<container_port_from_API_PORT_env>
            environment:
              - API_KEY=YOUR_VERY_STRONG_AND_SECRET_API_KEY
              - DATABASE_URL=sqlite+aiosqlite:///./data/database.db
              - API_PORT=8000
            volumes:
              - ./my_api_data_compose:/app/data # Persistent SQLite data
        ```

### B. Edge Devices (e.g., Jetson Nano, Raspberry Pi 4/5, Intel NUCs)

*   **Considerations**:
    *   **Resource Constraints**: Edge devices typically have limited CPU, RAM, and disk I/O. The API itself is relatively lightweight, but system overhead and other processes on the device must be considered.
    *   **Base Image**: The current `python:3.9-slim` base image is a good balance. For extremely constrained devices, further Docker image optimization (e.g., multi-stage builds, more minimal base images like Alpine Linux if all dependencies are compatible) could be explored. This is an advanced topic and out of scope for the current Dockerfile.
    *   **Database**: SQLite is highly suitable due to its low overhead and file-based nature. Ensure the storage medium (e.g., SD card, eMMC, SSD) is robust and of good quality to prevent data corruption, especially if there's frequent write activity (though the configuration API is not typically high-write).
    *   **Network Connectivity**: Edge devices may have intermittent or unreliable network connections. The API itself is stateless (configuration data is in the DB, `active_processing_tasks` is in-memory and reflects runtime state). If the API is primarily for local control of processing tasks on the edge device, this is generally acceptable. If it needs to sync with a central server, consider patterns for offline tolerance.
    *   **Hardware Acceleration**: Video processing tasks (which are conceptually separate from this API but might be initiated or controlled via it) often require hardware acceleration on edge devices (e.g., GPU on Jetson Nano). This is outside the scope of the API's deployment but critical for the overall application performance.
*   **Deployment**:
    *   Similar to a local server deployment using Docker.
    *   Ensure Docker is correctly installed for the device's architecture (e.g., ARM for Raspberry Pi/Jetson). The current Dockerfile is for x86_64 unless a multi-arch build process is used. For ARM devices, you might need to build the image on the device itself or use `docker buildx` for cross-compilation.
    *   Monitor resource usage (CPU, memory) carefully.

### C. Cloud Platforms (Generic Guidance)

Deploying to cloud platforms involves using their managed container services and, ideally, managed database services.

*   **General Steps**:
    1.  **Push Docker Image**: Build your image and push it to a container registry:
        *   Docker Hub (public or private)
        *   Amazon Elastic Container Registry (ECR)
        *   Azure Container Registry (ACR)
        *   Google Artifact Registry (GAR)
    2.  **Choose a Container Service**:
        *   **AWS**: Amazon ECS (with EC2 launch type or Fargate for serverless), Amazon EKS (Kubernetes).
        *   **Azure**: Azure Container Instances (ACI) for simple deployments, Azure Kubernetes Service (AKS).
        *   **Google Cloud**: Google Cloud Run (serverless), Google Kubernetes Engine (GKE).
    3.  **Configure the Service**:
        *   Point the service to your image in the registry.
        *   Set environment variables: `API_KEY`, `DATABASE_URL` (this should point to your cloud-managed database service), `API_PORT`.
        *   Manage secrets (API_KEY, DB credentials) using the cloud provider's secret management service (e.g., AWS Secrets Manager, Azure Key Vault, Google Secret Manager).
    4.  **Database**:
        *   Use a managed relational database service for production:
            *   AWS: Amazon RDS (PostgreSQL, MySQL)
            *   Azure: Azure Database for PostgreSQL/MySQL
            *   GCP: Google Cloud SQL (PostgreSQL, MySQL)
        *   Avoid using SQLite with volume mounts directly into most serverless container services like AWS Fargate or Google Cloud Run if multiple instances are expected or if data persistence requirements are complex. These services often have ephemeral storage or more complex persistent storage options not ideal for direct SQLite file paths without careful configuration. Managed databases are preferred.
    5.  **Networking**:
        *   Set up load balancers (e.g., AWS ALB, Azure Load Balancer, Google Cloud Load Balancing) for distributing traffic and providing a stable endpoint.
        *   Configure VPCs/VNETs, subnets, security groups/network security groups to control network access.
        *   Enable HTTPS using certificates managed by the cloud provider (e.g., AWS Certificate Manager, Azure App Service Certificates).

## 4. Minimum Hardware and Software Requirements (Estimates)

These are general estimates for running the backend API container itself. Actual video processing tasks controlled by this API will have significantly higher requirements, especially for GPU if AI models are involved.

*   **Software**:
    *   **Host OS**: Linux distribution (recommended for servers, cloud, edge), macOS/Windows (for local development/testing with Docker Desktop).
    *   **Docker Engine**: A recent version (e.g., 20.10 or newer).
*   **Hardware (API Container Only)**:
    *   **Local Server / Cloud Instance**:
        *   **CPU**: 1-2 virtual CPUs (vCPUs) should be sufficient for moderate API load.
        *   **RAM**: 512MB - 1GB. This depends on request volume, complexity of queries, and Python's memory usage.
        *   **Disk Space**: Approximately 1-2 GB for the Docker image and system overhead, plus additional space if using SQLite locally.
    *   **Edge Device (Typical)**:
        *   **CPU**: Examples include Raspberry Pi 4/5 (Quad-core ARM Cortex-A72/A76), Jetson Nano (Quad-core ARM Cortex-A57).
        *   **RAM**: 2GB minimum, 4GB+ recommended to comfortably run the OS, Docker, the API container, and potentially other local applications or lightweight processing.
        *   **Disk Space**: 16GB+ high-speed SD card or SSD (for OS, Docker runtime, image(s), and SQLite database).

## 5. General Constraints and Considerations

*   **SQLite Scalability**: While simple and effective for single-node deployments or edge devices with low-to-moderate traffic, SQLite is not designed for high-concurrency write scenarios or multi-server horizontal scaling of the API. For such cases, a dedicated relational database like PostgreSQL or MySQL is strongly recommended.
*   **Stateless API for Scaling**: The API application itself is largely stateless (configuration data is in the database). The `active_processing_tasks` set is currently in-memory. If horizontal scaling (running multiple instances of the API container) is required:
    *   A shared, robust database (PostgreSQL, MySQL) is essential for camera/policy/model configurations.
    *   The `active_processing_tasks` state would need to be moved to a shared store (e.g., Redis, or the database itself) if all API instances need a consistent view of active tasks. For simpler scenarios where processing tasks are tied to the API instance that started them, this might not be an immediate issue.
*   **Security**:
    *   **API Key**: Protect the `API_KEY` diligently. Use environment variables or secret management systems; do not hardcode it.
    *   **Database Credentials**: Similarly, protect database connection strings and credentials.
    *   **Network Security**: Implement firewalls, use HTTPS for API traffic (e.g., via a reverse proxy), and restrict database access to only necessary sources.
    *   **Secrets Management**: For production, use tools like HashiCorp Vault or cloud provider services (AWS Secrets Manager, Azure Key Vault, Google Secret Manager) to manage sensitive data like API keys and database passwords.
*   **Backup and Recovery**:
    *   **Database**: Implement regular backup procedures for your chosen database.
        *   SQLite: Back up the `.db` file. This can be done via file system snapshots if using a volume, or by periodically copying the file.
        *   PostgreSQL/MySQL: Use database-specific tools (e.g., `pg_dump`, `mysqldump`) or managed backup services from cloud providers.
    *   **Container Configuration**: Ensure your `docker run` commands or Docker Compose files are version controlled or backed up to easily recreate the container environment.

This guide provides a foundation for deploying the Video Analytics Backend API. Tailor the strategy to your specific environment, performance, and scalability requirements.
