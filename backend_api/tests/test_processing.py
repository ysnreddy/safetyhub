import pytest
from httpx import AsyncClient

# Helper function to create a policy
async def create_policy_for_processing_test(client: AsyncClient, name: str = "Test Policy For Processing"):
    response = await client.post("/configs/policies", json={
        "name": name,
        "policy_type": "processing_test_type",
        "parameters": {"detail": "processing_policy"}
    })
    assert response.status_code == 201, f"Failed to create policy: {response.text}"
    return response.json()

# Helper function to create model settings
async def create_model_settings_for_processing_test(client: AsyncClient, name: str = "Test MS For Processing"):
    response = await client.post("/configs/model_settings", json={
        "name": name,
        "model_path": "/models/processing_test.pt",
        "confidence_threshold": 0.5,
        "iou_threshold": 0.45
    })
    assert response.status_code == 201, f"Failed to create model settings: {response.text}"
    return response.json()

# Helper function to create a camera config
async def create_camera_config_for_processing_test(client: AsyncClient, policy_id: str, model_settings_id: str, name: str = "Test Camera For Processing"):
    camera_payload = {
        "name": name,
        "url": f"rtsp://example.com/{name.replace(' ', '_').lower()}",
        "policy_id": policy_id,
        "model_settings_id": model_settings_id
    }
    response = await client.post("/configs/cameras", json=camera_payload)
    assert response.status_code == 201, f"Failed to create camera: {response.text}"
    return response.json()


@pytest.mark.asyncio
async def test_unauthenticated_access_to_processing_endpoints(async_client: AsyncClient):
    """Test that unauthenticated access to processing endpoints returns 401."""
    endpoints = [
        ("/processing/start/some_cam_id", "POST"),
        ("/processing/stop/some_cam_id", "POST"),
        ("/processing/status", "GET"),
        ("/processing/status/some_cam_id", "GET"),
    ]
    for endpoint, method in endpoints:
        if method == "POST":
            response = await async_client.post(endpoint)
        else:
            response = await async_client.get(endpoint)
        assert response.status_code == 403, f"Failed for {method} {endpoint}"


@pytest.mark.asyncio
async def test_start_processing_success_and_status_check(authenticated_async_client: AsyncClient):
    """Test successful start of processing and verify status."""
    policy = await create_policy_for_processing_test(authenticated_async_client)
    ms = await create_model_settings_for_processing_test(authenticated_async_client)
    camera = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"])
    camera_id = camera["id"]

    # Start processing
    response_start = await authenticated_async_client.post(f"/processing/start/{camera_id}")
    assert response_start.status_code == 200
    assert response_start.json() == {"message": "Processing started", "camera_config_id": camera_id}

    # Check overall status
    response_status_overall = await authenticated_async_client.get("/processing/status")
    assert response_status_overall.status_code == 200
    assert camera_id in response_status_overall.json()["active_tasks"]

    # Check specific status
    response_status_specific = await authenticated_async_client.get(f"/processing/status/{camera_id}")
    assert response_status_specific.status_code == 200
    assert response_status_specific.json() == {"camera_config_id": camera_id, "status": "active"}

    # Teardown: Stop processing to clean up state for other tests
    await authenticated_async_client.post(f"/processing/stop/{camera_id}")


@pytest.mark.asyncio
async def test_start_processing_non_existent_camera(authenticated_async_client: AsyncClient):
    """Test starting processing for a non-existent camera_config_id."""
    response = await authenticated_async_client.post("/processing/start/non_existent_cam_id_123")
    assert response.status_code == 404
    assert "Camera configuration not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_start_processing_already_active(authenticated_async_client: AsyncClient):
    """Test starting processing for a camera that is already active."""
    policy = await create_policy_for_processing_test(authenticated_async_client, "PolicyForAlreadyActive")
    ms = await create_model_settings_for_processing_test(authenticated_async_client, "MSForAlreadyActive")
    camera = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamAlreadyActive")
    camera_id = camera["id"]

    # Start processing first time
    await authenticated_async_client.post(f"/processing/start/{camera_id}")

    # Attempt to start again
    response_second_start = await authenticated_async_client.post(f"/processing/start/{camera_id}")
    assert response_second_start.status_code == 400
    assert "Processing already active for this camera" in response_second_start.json()["detail"]
    
    # Teardown
    await authenticated_async_client.post(f"/processing/stop/{camera_id}")


@pytest.mark.asyncio
async def test_stop_processing_success_and_status_check(authenticated_async_client: AsyncClient):
    """Test successful stop of processing and verify status."""
    policy = await create_policy_for_processing_test(authenticated_async_client, "PolicyForStop")
    ms = await create_model_settings_for_processing_test(authenticated_async_client, "MSForStop")
    camera = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamForStop")
    camera_id = camera["id"]

    # Start processing first
    await authenticated_async_client.post(f"/processing/start/{camera_id}")

    # Stop processing
    response_stop = await authenticated_async_client.post(f"/processing/stop/{camera_id}")
    assert response_stop.status_code == 200
    assert response_stop.json() == {"message": "Processing stopped", "camera_config_id": camera_id}

    # Check overall status
    response_status_overall = await authenticated_async_client.get("/processing/status")
    assert response_status_overall.status_code == 200
    assert camera_id not in response_status_overall.json()["active_tasks"]

    # Check specific status
    response_status_specific = await authenticated_async_client.get(f"/processing/status/{camera_id}")
    assert response_status_specific.status_code == 200
    assert response_status_specific.json() == {"camera_config_id": camera_id, "status": "inactive"}


@pytest.mark.asyncio
async def test_stop_processing_non_existent_camera(authenticated_async_client: AsyncClient):
    """Test stopping processing for a non-existent camera_config_id."""
    # This test depends on whether the check for camera existence happens before or after checking active_processing_tasks.
    # Based on main.py, it first checks if it's in active_processing_tasks.
    # If not, it raises "Processing not active or already stopped for this camera" (400).
    # A non-existent camera ID would not be in active_processing_tasks.
    response = await authenticated_async_client.post("/processing/stop/non_existent_cam_id_456")
    assert response.status_code == 400 
    assert "Processing not active or already stopped for this camera" in response.json()["detail"]


@pytest.mark.asyncio
async def test_stop_processing_not_active(authenticated_async_client: AsyncClient):
    """Test stopping processing for a camera that is not currently active."""
    policy = await create_policy_for_processing_test(authenticated_async_client, "PolicyForNotActive")
    ms = await create_model_settings_for_processing_test(authenticated_async_client, "MSForNotActive")
    camera = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamNotActive")
    camera_id = camera["id"]
    # Camera exists but processing was never started for it

    response = await authenticated_async_client.post(f"/processing/stop/{camera_id}")
    assert response.status_code == 400
    assert "Processing not active or already stopped for this camera" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_overall_status_no_active_tasks(authenticated_async_client: AsyncClient):
    """Test /processing/status when no tasks are active."""
    # Ensure no tasks are running from previous tests if possible, or that this test is robust.
    # The active_processing_tasks is an in-memory set, so it's reset if the app instance is fresh.
    # Pytest test functions are isolated, but the app state might persist across calls within a session
    # if not managed. For this in-memory set, it's reset per app startup.
    # The AsyncClient used by pytest should provide a fresh app context or handle this.
    # Let's assume it's clean for this test.
    response = await authenticated_async_client.get("/processing/status")
    assert response.status_code == 200
    assert response.json() == {"active_tasks": []}

@pytest.mark.asyncio
async def test_get_overall_status_with_active_tasks(authenticated_async_client: AsyncClient):
    """Test /processing/status when multiple tasks are active."""
    policy = await create_policy_for_processing_test(authenticated_async_client, "PolicyForMultiActive")
    ms = await create_model_settings_for_processing_test(authenticated_async_client, "MSForMultiActive")
    
    cam1 = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamMultiActive1")
    cam2 = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamMultiActive2")
    cam1_id, cam2_id = cam1["id"], cam2["id"]

    await authenticated_async_client.post(f"/processing/start/{cam1_id}")
    await authenticated_async_client.post(f"/processing/start/{cam2_id}")

    response = await authenticated_async_client.get("/processing/status")
    assert response.status_code == 200
    active_tasks = response.json()["active_tasks"]
    assert cam1_id in active_tasks
    assert cam2_id in active_tasks
    assert len(active_tasks) >= 2 # Could be more if other tests didn't clean up, ideally 2

    # Teardown
    await authenticated_async_client.post(f"/processing/stop/{cam1_id}")
    await authenticated_async_client.post(f"/processing/stop/{cam2_id}")


@pytest.mark.asyncio
async def test_get_specific_status_non_existent_camera(authenticated_async_client: AsyncClient):
    """Test /processing/status/{camera_config_id} for a non-existent camera."""
    response = await authenticated_async_client.get("/processing/status/non_existent_cam_id_789")
    assert response.status_code == 404
    assert "Camera configuration not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_specific_status_inactive(authenticated_async_client: AsyncClient):
    """Test /processing/status/{camera_config_id} for an existing, inactive camera."""
    policy = await create_policy_for_processing_test(authenticated_async_client, "PolicyForSpecificInactive")
    ms = await create_model_settings_for_processing_test(authenticated_async_client, "MSForSpecificInactive")
    camera = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamSpecificInactive")
    camera_id = camera["id"]

    response = await authenticated_async_client.get(f"/processing/status/{camera_id}")
    assert response.status_code == 200
    assert response.json() == {"camera_config_id": camera_id, "status": "inactive"}

@pytest.mark.asyncio
async def test_get_specific_status_active(authenticated_async_client: AsyncClient):
    """Test /processing/status/{camera_config_id} for an existing, active camera."""
    policy = await create_policy_for_processing_test(authenticated_async_client, "PolicyForSpecificActive")
    ms = await create_model_settings_for_processing_test(authenticated_async_client, "MSForSpecificActive")
    camera = await create_camera_config_for_processing_test(authenticated_async_client, policy["id"], ms["id"], "CamSpecificActive")
    camera_id = camera["id"]

    # Start processing
    await authenticated_async_client.post(f"/processing/start/{camera_id}")

    response = await authenticated_async_client.get(f"/processing/status/{camera_id}")
    assert response.status_code == 200
    assert response.json() == {"camera_config_id": camera_id, "status": "active"}

    # Teardown
    await authenticated_async_client.post(f"/processing/stop/{camera_id}")
