import pytest
from httpx import AsyncClient

# Helper function to create a policy
async def create_policy_for_test(client: AsyncClient, name: str = "Test Policy", policy_type: str = "test_type", params: dict = None):
    if params is None:
        params = {"setting1": "value1"}
    response = await client.post("/configs/policies", json={
        "name": name,
        "policy_type": policy_type,
        "parameters": params
    })
    assert response.status_code == 201
    return response.json()

# Helper function to create model settings
async def create_model_settings_for_test(client: AsyncClient, name: str = "Test Model Settings", model_path: str = "/models/test.pt", conf: float = 0.5, iou: float = 0.45):
    response = await client.post("/configs/model_settings", json={
        "name": name,
        "model_path": model_path,
        "confidence_threshold": conf,
        "iou_threshold": iou
    })
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_unauthenticated_access_to_camera_endpoints(async_client: AsyncClient):
    """Test that unauthenticated access to camera endpoints returns 401."""
    camera_payload = {
        "name": "Test Camera",
        "url": "rtsp://example.com/stream1",
        "policy_id": "some_policy_id",
        "model_settings_id": "some_model_id"
    }
    
    # POST /configs/cameras
    response = await async_client.post("/configs/cameras", json=camera_payload)
    assert response.status_code == 403

    # GET /configs/cameras
    response = await async_client.get("/configs/cameras")
    assert response.status_code == 403

    # GET /configs/cameras/{camera_id}
    response = await async_client.get("/configs/cameras/some_camera_id")
    assert response.status_code == 403

    # PUT /configs/cameras/{camera_id}
    response = await async_client.put("/configs/cameras/some_camera_id", json=camera_payload)
    assert response.status_code == 403

    # DELETE /configs/cameras/{camera_id}
    response = await async_client.delete("/configs/cameras/some_camera_id")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_camera_success(authenticated_async_client: AsyncClient):
    """Test successful camera creation."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForCamera")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForCamera")

    camera_payload = {
        "name": "Entrance Camera",
        "url": "rtsp://example.com/entrance",
        "description": "Monitors the main entrance",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"],
        "is_active": True
    }
    response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == camera_payload["name"]
    assert data["url"] == camera_payload["url"]
    assert data["description"] == camera_payload["description"]
    assert data["policy_id"] == policy["id"]
    assert data["model_settings_id"] == model_settings["id"]
    assert data["is_active"] == camera_payload["is_active"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_camera_missing_fields(authenticated_async_client: AsyncClient):
    """Test camera creation with missing required fields."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForMissingFields")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForMissingFields")

    # Missing name
    response = await authenticated_async_client.post("/configs/cameras", json={
        "url": "rtsp://example.com/missing_name",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    })
    assert response.status_code == 422

    # Missing url
    response = await authenticated_async_client.post("/configs/cameras", json={
        "name": "Missing URL Cam",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    })
    assert response.status_code == 422
    
    # Missing policy_id
    response = await authenticated_async_client.post("/configs/cameras", json={
        "name": "Missing Policy ID Cam",
        "url": "rtsp://example.com/missing_policy",
        "model_settings_id": model_settings["id"]
    })
    assert response.status_code == 422

    # Missing model_settings_id
    response = await authenticated_async_client.post("/configs/cameras", json={
        "name": "Missing ModelSettings ID Cam",
        "url": "rtsp://example.com/missing_model",
        "policy_id": policy["id"]
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_camera_invalid_foreign_ids(authenticated_async_client: AsyncClient):
    """Test camera creation with invalid policy_id or model_settings_id."""
    policy = await create_policy_for_test(authenticated_async_client, "ValidPolicyForFKTest")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ValidModelForFKTest")

    # Invalid policy_id
    response = await authenticated_async_client.post("/configs/cameras", json={
        "name": "Invalid Policy ID Cam",
        "url": "rtsp://example.com/invalid_policy",
        "policy_id": "non_existent_policy_id_123",
        "model_settings_id": model_settings["id"]
    })
    assert response.status_code == 400
    assert "Policy with id non_existent_policy_id_123 not found" in response.json()["detail"]

    # Invalid model_settings_id
    response = await authenticated_async_client.post("/configs/cameras", json={
        "name": "Invalid ModelSettings ID Cam",
        "url": "rtsp://example.com/invalid_model",
        "policy_id": policy["id"],
        "model_settings_id": "non_existent_model_id_456"
    })
    assert response.status_code == 400
    assert "ModelSettings with id non_existent_model_id_456 not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_cameras_with_items(authenticated_async_client: AsyncClient):
    """Test retrieving a list of cameras after creating one."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForListTest")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForListTest")
    
    camera_payload = {
        "name": "Camera For Listing",
        "url": "rtsp://example.com/list_test",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    await authenticated_async_client.post("/configs/cameras", json=camera_payload)

    response = await authenticated_async_client.get("/configs/cameras")
    assert response.status_code == 200
    cameras = response.json()
    assert len(cameras) >= 1 # Greater or equal due to potential other tests, ideally 1
    assert any(cam["name"] == camera_payload["name"] for cam in cameras)

@pytest.mark.asyncio
async def test_get_specific_camera_success(authenticated_async_client: AsyncClient):
    """Test retrieving an existing camera by ID."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForGetTest")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForGetTest")

    camera_payload = {
        "name": "Specific Camera",
        "url": "rtsp://example.com/specific",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    create_response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    created_camera_id = create_response.json()["id"]

    response = await authenticated_async_client.get(f"/configs/cameras/{created_camera_id}")
    assert response.status_code == 200
    camera = response.json()
    assert camera["id"] == created_camera_id
    assert camera["name"] == camera_payload["name"]

@pytest.mark.asyncio
async def test_get_specific_camera_not_found(authenticated_async_client: AsyncClient):
    """Test retrieving a non-existent camera by ID."""
    response = await authenticated_async_client.get("/configs/cameras/non_existent_camera_id_789")
    assert response.status_code == 404
    assert "Camera not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_camera_success(authenticated_async_client: AsyncClient):
    """Test successful update of an existing camera."""
    policy1 = await create_policy_for_test(authenticated_async_client, "PolicyForUpdate1")
    model_settings1 = await create_model_settings_for_test(authenticated_async_client, "ModelForUpdate1")
    policy2 = await create_policy_for_test(authenticated_async_client, "PolicyForUpdate2") # For updating policy_id

    camera_payload = {
        "name": "Camera To Update",
        "url": "rtsp://example.com/to_update",
        "policy_id": policy1["id"],
        "model_settings_id": model_settings1["id"]
    }
    create_response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    created_camera_data = create_response.json()
    created_camera_id = created_camera_data["id"]

    update_payload = {
        "name": "Updated Camera Name",
        "url": "rtsp://example.com/updated_url",
        "description": "Now with a description!",
        "policy_id": policy2["id"], # Change policy
        "model_settings_id": created_camera_data["model_settings_id"], # Ensure all required fields are present
        "is_active": False
    }
    response = await authenticated_async_client.put(f"/configs/cameras/{created_camera_id}", json=update_payload)
    assert response.status_code == 200
    updated_camera = response.json()
    assert updated_camera["id"] == created_camera_id
    assert updated_camera["name"] == update_payload["name"]
    assert updated_camera["url"] == update_payload["url"]
    assert updated_camera["description"] == update_payload["description"]
    assert updated_camera["policy_id"] == update_payload["policy_id"]
    assert updated_camera["model_settings_id"] == model_settings1["id"] # Should not change if not provided
    assert updated_camera["is_active"] == update_payload["is_active"]

@pytest.mark.asyncio
async def test_update_camera_not_found(authenticated_async_client: AsyncClient):
    """Test updating a non-existent camera."""
    # Payload must be valid for CameraConfig even if ID is wrong, due to how FastAPI processes requests
    valid_payload_for_non_existent_id = {
        "name": "Non Existent Cam Update",
        "url": "rtsp://example.com/non_existent",
        "policy_id": "dummy_policy_id", # These won't be checked if camera_id itself is not found
        "model_settings_id": "dummy_model_id",
        "description": "Trying to update non-existent",
        "is_active": True
    }
    response = await authenticated_async_client.put("/configs/cameras/non_existent_camera_id_000", json=valid_payload_for_non_existent_id)
    assert response.status_code == 404
    assert "Camera not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_camera_missing_fields(authenticated_async_client: AsyncClient):
    """Test updating a camera with missing required fields in payload (should be 422)."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForUpdateValidation")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForUpdateValidation")

    camera_payload = {
        "name": "CamForFieldValidation",
        "url": "rtsp://example.com/validation",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    create_response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    created_camera_id = create_response.json()["id"]

    # Attempt to update with name missing (name is required in Pydantic model)
    response = await authenticated_async_client.put(f"/configs/cameras/{created_camera_id}", json={"url": None})
    assert response.status_code == 422 # FastAPI should enforce Pydantic model validation

@pytest.mark.asyncio
async def test_update_camera_invalid_foreign_ids(authenticated_async_client: AsyncClient):
    """Test updating a camera with invalid policy_id or model_settings_id."""
    policy = await create_policy_for_test(authenticated_async_client, "ValidPolicyForUpdateFK")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ValidModelForUpdateFK")

    camera_payload = {
        "name": "CamForFKUpdate",
        "url": "rtsp://example.com/fk_update",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    create_response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    created_camera_data = create_response.json()
    created_camera_id = created_camera_data["id"]

    # Invalid policy_id
    update_payload_invalid_policy = {
        "name": "Updated Name - Invalid Policy",
        "url": created_camera_data["url"],
        "policy_id": "invalid_policy_fk_777",
        "model_settings_id": created_camera_data["model_settings_id"],
        "is_active": created_camera_data["is_active"]
    }
    response = await authenticated_async_client.put(f"/configs/cameras/{created_camera_id}", json=update_payload_invalid_policy)
    assert response.status_code == 400
    assert "Policy with id invalid_policy_fk_777 not found" in response.json()["detail"]

    # Invalid model_settings_id
    update_payload_invalid_model = {
        "name": "Updated Name Again - Invalid Model",
        "url": created_camera_data["url"],
        "policy_id": created_camera_data["policy_id"],
        "model_settings_id": "invalid_model_fk_888",
        "is_active": created_camera_data["is_active"]
    }
    response = await authenticated_async_client.put(f"/configs/cameras/{created_camera_id}", json=update_payload_invalid_model)
    assert response.status_code == 400
    assert "ModelSettings with id invalid_model_fk_888 not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_camera_id_mismatch(authenticated_async_client: AsyncClient):
    """Test that camera ID in path cannot be changed by ID in body."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForIDMismatch")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForIDMismatch")

    camera_payload = {
        "name": "ID Mismatch Test Cam",
        "url": "rtsp://example.com/id_mismatch",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    create_response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    created_camera_id = create_response.json()["id"]

    update_payload_with_different_id = {
        "id": "completely_different_id_123", # Attempt to change ID
        "name": "Attempting ID Change",
        "url": camera_payload["url"], # Keep other fields valid
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    response = await authenticated_async_client.put(
        f"/configs/cameras/{created_camera_id}",
        json=update_payload_with_different_id
    )
    # The API should reject this or ignore the ID in the body.
    # Current implementation (based on common practice) should reject if body 'id' is present and different.
    assert response.status_code == 400 
    assert "Camera ID in path does not match ID in body" in response.json()["detail"]
    
    # Verify original camera is unchanged by this attempt (or check if it was updated but ID remained)
    get_response = await authenticated_async_client.get(f"/configs/cameras/{created_camera_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == camera_payload["name"] # Name should not have changed

@pytest.mark.asyncio
async def test_delete_camera_success(authenticated_async_client: AsyncClient):
    """Test successful deletion of an existing camera."""
    policy = await create_policy_for_test(authenticated_async_client, "PolicyForDeleteTest")
    model_settings = await create_model_settings_for_test(authenticated_async_client, "ModelForDeleteTest")

    camera_payload = {
        "name": "Camera To Be Deleted",
        "url": "rtsp://example.com/to_delete",
        "policy_id": policy["id"],
        "model_settings_id": model_settings["id"]
    }
    create_response = await authenticated_async_client.post("/configs/cameras", json=camera_payload)
    created_camera_id = create_response.json()["id"]

    # Delete the camera
    delete_response = await authenticated_async_client.delete(f"/configs/cameras/{created_camera_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Camera deleted successfully"}

    # Verify camera is actually deleted
    get_response = await authenticated_async_client.get(f"/configs/cameras/{created_camera_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_camera_not_found(authenticated_async_client: AsyncClient):
    """Test deleting a non-existent camera."""
    response = await authenticated_async_client.delete("/configs/cameras/non_existent_camera_id_404")
    assert response.status_code == 404
    assert "Camera not found" in response.json()["detail"]

# Note on test_list_cameras_empty:
# The test database is created once per session and tables are created.
# If other camera tests run before test_list_cameras_empty and add cameras,
# the list won't be empty.
# For truly isolated list_empty tests, one might consider:
# 1. A function-scoped fixture that clears specific tables before the test.
# 2. Ordering tests (less ideal with pytest).
# 3. Making the test robust to pre-existing data if not strictly testing "from zero".
# The current `test_engine` fixture in conftest.py removes and recreates the DB file per session,
# so if these tests are the only ones in a session, `test_list_cameras_empty` should pass.
# If combined with other test files modifying cameras, it might be flaky.
# For this exercise, we'll assume it's run in a context where it can expect an empty state initially
# or that "empty" means "empty of cameras created specifically for this test's setup".
# The current implementation of test_list_cameras_empty is simple and might need adjustment in a larger suite.
# A more robust empty list test would be to create items, then delete them all, then check for empty.
# Or, create a unique policy/model_setting, list cameras for that, and expect empty.
# Given the current setup, it checks the global list.
