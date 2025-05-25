from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

from .database import database, create_db_and_tables
from .models import cameras as cameras_table, policies as policies_table, model_settings as model_settings_table

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    print("Error: API_KEY environment variable not set.")
    exit(1) # Exit if API_KEY is not configured

API_KEY_NAME = "X-API-Key"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Depends(api_key_header_auth)):
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Header"},
        )
    return api_key_header

app = FastAPI(
    title="Video Analytics Backend API",
    version="1.0.0",
    description="API for managing video analytics configurations (cameras, policies, models) and controlling video processing tasks. Most endpoints require an API key passed in the `X-API-Key` header.",
    dependencies=[Depends(get_api_key)] # Apply to all routes by default
)

# Allow /docs, /redoc, and /health to be accessed without API key
# We achieve this by creating a separate app for these routes or by overriding dependency for these specific routes.
# For simplicity in this context, we will re-declare routes that should be public without the global dependency.
# A more complex app might use APIRouter with different dependencies.

# Pydantic Models
class CameraConfig(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the camera configuration (auto-generated on creation).")
    name: str = Field(..., description="User-friendly name for the camera.")
    url: str = Field(..., description="URL of the video stream (e.g., RTSP link).")
    description: Optional[str] = Field(None, description="Optional detailed description of the camera.")
    policy_id: str = Field(..., description="ID of the policy to apply to this camera.")
    model_settings_id: str = Field(..., description="ID of the model settings to use for this camera.")
    is_active: bool = Field(True, description="Represents if the camera is generally available for processing (persistent setting). Does not reflect real-time processing status.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Entrance Camera",
                "url": "rtsp://example.com/stream1",
                "description": "Monitors the main entrance",
                "policy_id": "policy_uuid_123",
                "model_settings_id": "model_uuid_456",
                "is_active": True,
            }
        }
    )

class Policy(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the policy (auto-generated on creation).")
    name: str = Field(..., description="User-friendly name for the policy.")
    policy_type: str = Field(..., description="Type of policy (e.g., 'intrusion_detection', 'loitering_detection').")
    parameters: Dict[str, Any] = Field(..., description="Dictionary of parameters specific to the policy type.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Standard Intrusion Policy",
                "policy_type": "intrusion_detection",
                "parameters": {"sensitivity": "high", "detection_zones": [{"x":0,"y":0,"w":100,"h":100}]},
            }
        }
    )

class ModelSettings(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the model settings (auto-generated on creation).")
    name: str = Field(..., description="User-friendly name for the model settings.")
    model_path: str = Field(..., description="Path to the model file (e.g., on a shared volume or URL).")
    confidence_threshold: float = Field(..., description="Confidence threshold for detections (0.0 to 1.0).")
    iou_threshold: float = Field(..., description="Intersection over Union (IoU) threshold for non-maximum suppression (0.0 to 1.0).")
    other_params: Optional[Dict[str, Any]] = Field(None, description="Optional dictionary for other model-specific parameters.")

    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "name": "Default YOLOv8 Settings",
                "model_path": "/models/yolov8m.pt",
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45,
                "other_params": {"resolution": "1280x720"}
            }
        }
    )

# In-memory set for active processing tasks
# TODO: This could be moved to the database for full persistence if needed,
# especially if the application might be scaled or needs to recover this state after a restart.
active_processing_tasks: set[str] = set()

@asynccontextmanager
async def lifespan(app_lifespan: FastAPI): # Renamed 'app' to 'app_lifespan' to avoid conflict with global 'app'
    # Startup
    print("Connecting to database...")
    await database.connect()
    print("Creating database tables...")
    create_db_and_tables() # This is a synchronous call, run once
    print("Database connected and tables created.")
    yield
    # Shutdown
    print("Disconnecting from database...")
    await database.disconnect()
    print("Database disconnected.")

app = FastAPI(
    title="Video Analytics Backend API",
    version="1.0.0",
    description="API for managing video analytics configurations (cameras, policies, models) and controlling video processing tasks. Most endpoints require an API key passed in the `X-API-Key` header.",
    dependencies=[Depends(get_api_key)], # Apply to all routes by default
    lifespan=lifespan # Use the new lifespan context manager
)

# Public Endpoints (No API Key Required)
# To make these public, we define them on a router that doesn't have the global dependency,
# or we explicitly pass an empty list of dependencies to them.
# For this setup, we will make them part of the main app but specifically exclude the global dependency
# by re-registering them *after* the app has been initialized with the global dependency. This is a bit of a workaround.
# A cleaner way with multiple routers: public_router = APIRouter(); @public_router.get("/health") ...; app.include_router(public_router)
# For now, we will redefine the routes with `dependencies=[]` to exclude them from global auth.

@app.get("/health",
    dependencies=[], # Override global dependency to make it public
    summary="Health Check",
    description="Performs a basic health check of the API and its database connection.",
    tags=["Public"]
)
async def health_check():
    try:
        await database.execute("SELECT 1")
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok", "database_status": db_status}

# Note: /docs and /redoc are automatically excluded by FastAPI when global dependencies are used
# if `auto_error` is True for the security scheme, which it is by default for APIKeyHeader.
# If they were not, you might need to use a more complex setup with routers. FastAPI's default behavior
# with security utilities usually handles OpenAPI docs access correctly for /docs and /redoc.


# CRUD Endpoints for Policies
@app.post("/configs/policies",
    response_model=Policy,
    status_code=201,
    summary="Create Policy",
    description="Creates a new policy configuration. A unique ID will be generated.",
    tags=["Configuration - Policies"]
)
async def create_policy(policy: Policy):
    new_id = str(uuid.uuid4())
    query = policies_table.insert().values(
        id=new_id,
        name=policy.name,
        policy_type=policy.policy_type,
        parameters=policy.parameters,
    )
    await database.execute(query)
    return {**policy.model_dump(), "id": new_id}

@app.get("/configs/policies",
    response_model=List[Policy],
    summary="List Policies",
    description="Retrieves a list of all policy configurations.",
    tags=["Configuration - Policies"]
)
async def list_policies():
    query = policies_table.select()
    return await database.fetch_all(query)

@app.get("/configs/policies/{policy_id}",
    response_model=Policy,
    summary="Get Policy",
    description="Retrieves a specific policy configuration by its ID.",
    tags=["Configuration - Policies"]
)
async def get_policy(policy_id: str):
    query = policies_table.select().where(policies_table.c.id == policy_id)
    db_policy = await database.fetch_one(query)
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return db_policy

@app.put("/configs/policies/{policy_id}",
    response_model=Policy,
    summary="Update Policy",
    description="Updates an existing policy configuration by its ID.",
    tags=["Configuration - Policies"]
)
async def update_policy(policy_id: str, policy_update: Policy):
    query = policies_table.select().where(policies_table.c.id == policy_id)
    db_policy = await database.fetch_one(query)
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    update_data = policy_update.model_dump(exclude_unset=True)
    if "id" in update_data and update_data["id"] != policy_id:
         raise HTTPException(status_code=400, detail="Policy ID in path does not match ID in body if provided")
    update_data.pop("id", None)

    query_update = (
        policies_table.update()
        .where(policies_table.c.id == policy_id)
        .values(**update_data)
    )
    await database.execute(query_update)
    updated_db_policy = await database.fetch_one(policies_table.select().where(policies_table.c.id == policy_id))
    if updated_db_policy is None: # Should not happen if update succeeded and ID is correct
        raise HTTPException(status_code=404, detail="Policy not found after update attempt.")
    return Policy(**updated_db_policy)


@app.delete("/configs/policies/{policy_id}",
    status_code=200, # Or 204 if no content is returned
    summary="Delete Policy",
    description="Deletes a policy configuration by its ID.",
    tags=["Configuration - Policies"]
)
async def delete_policy(policy_id: str):
    query = policies_table.select().where(policies_table.c.id == policy_id)
    db_policy = await database.fetch_one(query)
    if db_policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")

    delete_query = policies_table.delete().where(policies_table.c.id == policy_id)
    await database.execute(delete_query)
    return {"message": "Policy deleted successfully"}

# CRUD Endpoints for Model Settings
@app.post("/configs/model_settings",
    response_model=ModelSettings,
    status_code=201,
    summary="Create Model Settings",
    description="Creates a new model settings configuration. A unique ID will be generated.",
    tags=["Configuration - Model Settings"]
)
async def create_model_settings(settings: ModelSettings):
    new_id = str(uuid.uuid4())
    query = model_settings_table.insert().values(
        id=new_id,
        name=settings.name,
        model_path=settings.model_path,
        confidence_threshold=settings.confidence_threshold,
        iou_threshold=settings.iou_threshold,
        other_params=settings.other_params,
    )
    await database.execute(query)
    return {**settings.model_dump(), "id": new_id}

@app.get("/configs/model_settings",
    response_model=List[ModelSettings],
    summary="List Model Settings",
    description="Retrieves a list of all model settings configurations.",
    tags=["Configuration - Model Settings"]
)
async def list_model_settings():
    query = model_settings_table.select()
    return await database.fetch_all(query)

@app.get("/configs/model_settings/{model_settings_id}",
    response_model=ModelSettings,
    summary="Get Model Settings",
    description="Retrieves a specific model settings configuration by its ID.",
    tags=["Configuration - Model Settings"]
)
async def get_model_settings(model_settings_id: str):
    query = model_settings_table.select().where(model_settings_table.c.id == model_settings_id)
    db_settings = await database.fetch_one(query)
    if db_settings is None:
        raise HTTPException(status_code=404, detail="ModelSettings not found")
    return db_settings

@app.put("/configs/model_settings/{model_settings_id}",
    response_model=ModelSettings,
    summary="Update Model Settings",
    description="Updates an existing model settings configuration by its ID.",
    tags=["Configuration - Model Settings"]
)
async def update_model_settings(model_settings_id: str, settings_update: ModelSettings):
    query = model_settings_table.select().where(model_settings_table.c.id == model_settings_id)
    db_settings = await database.fetch_one(query)
    if db_settings is None:
        raise HTTPException(status_code=404, detail="ModelSettings not found")

    update_data = settings_update.model_dump(exclude_unset=True)
    if "id" in update_data and update_data["id"] != model_settings_id:
        raise HTTPException(status_code=400, detail="ModelSettings ID in path does not match ID in body")
    update_data.pop("id", None)

    query_update = (
        model_settings_table.update()
        .where(model_settings_table.c.id == model_settings_id)
        .values(**update_data)
    )
    await database.execute(query_update)
    updated_db_settings = await database.fetch_one(model_settings_table.select().where(model_settings_table.c.id == model_settings_id))
    if updated_db_settings is None:  # Should not happen
        raise HTTPException(status_code=404, detail="ModelSettings not found after update attempt.")
    return ModelSettings(**updated_db_settings)

@app.delete("/configs/model_settings/{model_settings_id}",
    status_code=200, # Or 204
    summary="Delete Model Settings",
    description="Deletes a model settings configuration by its ID.",
    tags=["Configuration - Model Settings"]
)
async def delete_model_settings(model_settings_id: str):
    query = model_settings_table.select().where(model_settings_table.c.id == model_settings_id)
    db_settings = await database.fetch_one(query)
    if db_settings is None:
        raise HTTPException(status_code=404, detail="ModelSettings not found")

    delete_query = model_settings_table.delete().where(model_settings_table.c.id == model_settings_id)
    await database.execute(delete_query)
    return {"message": "ModelSettings deleted successfully"}


# CRUD Endpoints for Cameras
@app.post("/configs/cameras",
    response_model=CameraConfig,
    status_code=201,
    summary="Create Camera Configuration",
    description="Creates a new camera configuration. A unique ID will be generated. `policy_id` and `model_settings_id` must refer to existing configurations.",
    tags=["Configuration - Cameras"]
)
async def create_camera_config(camera: CameraConfig):
    policy_query = policies_table.select().where(policies_table.c.id == camera.policy_id)
    if not await database.fetch_one(policy_query):
        raise HTTPException(status_code=400, detail=f"Policy with id {camera.policy_id} not found.")
    model_settings_query = model_settings_table.select().where(model_settings_table.c.id == camera.model_settings_id)
    if not await database.fetch_one(model_settings_query):
        raise HTTPException(status_code=400, detail=f"ModelSettings with id {camera.model_settings_id} not found.")

    new_id = str(uuid.uuid4())
    query = cameras_table.insert().values(
        id=new_id,
        name=camera.name,
        url=camera.url,
        description=camera.description,
        policy_id=camera.policy_id,
        model_settings_id=camera.model_settings_id,
        is_active=camera.is_active,
    )
    await database.execute(query)
    return {**camera.model_dump(), "id": new_id}

@app.get("/configs/cameras",
    response_model=List[CameraConfig],
    summary="List Camera Configurations",
    description="Retrieves a list of all camera configurations.",
    tags=["Configuration - Cameras"]
)
async def list_camera_configs():
    query = cameras_table.select()
    return await database.fetch_all(query)

@app.get("/configs/cameras/{camera_id}",
    response_model=CameraConfig,
    summary="Get Camera Configuration",
    description="Retrieves a specific camera configuration by its ID.",
    tags=["Configuration - Cameras"]
)
async def get_camera_config(camera_id: str):
    query = cameras_table.select().where(cameras_table.c.id == camera_id)
    db_camera = await database.fetch_one(query)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")
    return db_camera

@app.put("/configs/cameras/{camera_id}",
    response_model=CameraConfig,
    summary="Update Camera Configuration",
    description="Updates an existing camera configuration by its ID. `policy_id` and `model_settings_id`, if provided, must refer to existing configurations.",
    tags=["Configuration - Cameras"]
)
async def update_camera_config(camera_id: str, camera_update: CameraConfig):
    query = cameras_table.select().where(cameras_table.c.id == camera_id)
    db_camera = await database.fetch_one(query)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    update_data = camera_update.model_dump(exclude_unset=True)
    if "id" in update_data and update_data["id"] != camera_id:
        raise HTTPException(status_code=400, detail="Camera ID in path does not match ID in body")
    update_data.pop("id", None)

    if "policy_id" in update_data:
        policy_query = policies_table.select().where(policies_table.c.id == update_data["policy_id"])
        if not await database.fetch_one(policy_query):
            raise HTTPException(status_code=400, detail=f"Policy with id {update_data['policy_id']} not found.")
    if "model_settings_id" in update_data:
        model_settings_query = model_settings_table.select().where(model_settings_table.c.id == update_data["model_settings_id"])
        if not await database.fetch_one(model_settings_query):
            raise HTTPException(status_code=400, detail=f"ModelSettings with id {update_data['model_settings_id']} not found.")

    query_update = (
        cameras_table.update()
        .where(cameras_table.c.id == camera_id)
        .values(**update_data)
    )
    await database.execute(query_update)
    updated_db_camera = await database.fetch_one(cameras_table.select().where(cameras_table.c.id == camera_id))
    if updated_db_camera is None: # Should not happen
        raise HTTPException(status_code=404, detail="Camera not found after update attempt.")
    return CameraConfig(**updated_db_camera)

@app.delete("/configs/cameras/{camera_id}",
    status_code=200, # Or 204
    summary="Delete Camera Configuration",
    description="Deletes a camera configuration by its ID.",
    tags=["Configuration - Cameras"]
)
async def delete_camera_config(camera_id: str):
    query = cameras_table.select().where(cameras_table.c.id == camera_id)
    db_camera = await database.fetch_one(query)
    if db_camera is None:
        raise HTTPException(status_code=404, detail="Camera not found")

    delete_query = cameras_table.delete().where(cameras_table.c.id == camera_id)
    await database.execute(delete_query)
    return {"message": "Camera deleted successfully"}


# Video Processing Control Endpoints
@app.post("/processing/start/{camera_config_id}",
    status_code=200,
    summary="Start Video Processing",
    description="Starts the video processing task for a specified camera configuration ID. The camera configuration must exist.",
    response_model=Dict[str, str],
    tags=["Video Processing Control"]
)
async def start_processing(camera_config_id: str):
    query = cameras_table.select().where(cameras_table.c.id == camera_config_id)
    camera_exists = await database.fetch_one(query)
    if not camera_exists:
        raise HTTPException(status_code=404, detail="Camera configuration not found")
    
    if camera_config_id in active_processing_tasks:
        raise HTTPException(status_code=400, detail="Processing already active for this camera")
    
    active_processing_tasks.add(camera_config_id)
    return {"message": "Processing started", "camera_config_id": camera_config_id}

@app.post("/processing/stop/{camera_config_id}",
    status_code=200,
    summary="Stop Video Processing",
    description="Stops the video processing task for a specified camera configuration ID if it is currently active.",
    response_model=Dict[str, str],
    tags=["Video Processing Control"]
)
async def stop_processing(camera_config_id: str):
    if camera_config_id not in active_processing_tasks:
        raise HTTPException(status_code=400, detail="Processing not active or already stopped for this camera")

    active_processing_tasks.remove(camera_config_id)
    return {"message": "Processing stopped", "camera_config_id": camera_config_id}

@app.get("/processing/status",
    response_model=Dict[str, List[str]],
    summary="Overall Processing Status",
    description="Retrieves a list of camera configuration IDs for which processing tasks are currently active (in-memory state).",
    tags=["Video Processing Control"]
)
async def get_overall_status():
    return {"active_tasks": list(active_processing_tasks)}

@app.get("/processing/status/{camera_config_id}",
    response_model=Dict[str, str],
    summary="Specific Camera Processing Status",
    description="Retrieves the processing status ('active' or 'inactive') for a specific camera configuration ID. The camera configuration must exist.",
    tags=["Video Processing Control"]
)
async def get_specific_status(camera_config_id: str):
    query = cameras_table.select().where(cameras_table.c.id == camera_config_id)
    camera_exists = await database.fetch_one(query)
    if not camera_exists:
        raise HTTPException(status_code=404, detail="Camera configuration not found")
    
    if camera_config_id in active_processing_tasks:
        return {"camera_config_id": camera_config_id, "status": "active"}
    else:
        return {"camera_config_id": camera_config_id, "status": "inactive"}

# The /docs and /redoc endpoints are automatically generated by FastAPI.
# If `auto_error=False` was set on APIKeyHeader, or if using a more manual check,
# you would need to add `dependencies=[]` to the routes for /docs and /redoc if they were
# defined manually. However, FastAPI's default behavior with security utilities usually
# handles OpenAPI docs access correctly.
# For instance, if you had a custom router for docs:
# from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
# @app.get("/docs", include_in_schema=False, dependencies=[])
# async def custom_swagger_ui_html():
# return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - Swagger UI")
#
# @app.get("/redoc", include_in_schema=False, dependencies=[])
# async def redoc_html():
# return get_redoc_html(openapi_url=app.openapi_url, title=app.title + " - ReDoc")
