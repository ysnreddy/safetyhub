import pytest
from httpx import AsyncClient

# Helper function to create model settings (can also be used by other test files if moved to conftest)
async def create_model_settings_for_test(client: AsyncClient, name: str = "Test Model Settings", model_path: str = "/models/test.pt", conf: float = 0.5, iou: float = 0.45, other_params: dict = None):
    payload = {
        "name": name,
        "model_path": model_path,
        "confidence_threshold": conf,
        "iou_threshold": iou
    }
    if other_params is not None:
        payload["other_params"] = other_params
        
    response = await client.post("/configs/model_settings", json=payload)
    assert response.status_code == 201, f"Failed to create model settings: {response.text}"
    return response.json()

# Helper function to create a policy (needed for creating a camera that uses model settings)
async def create_policy_for_test(client: AsyncClient, name: str = "Test Policy For MS Test", policy_type: str = "test_type_ms", params: dict = None):
    if params is None:
        params = {"setting1_ms": "value1_ms"}
    response = await client.post("/configs/policies", json={
        "name": name,
        "policy_type": policy_type,
        "parameters": params
    })
    assert response.status_code == 201, f"Failed to create policy: {response.text}"
    return response.json()

# Helper function to create a camera (needed for testing deletion of in-use model settings)
async def create_camera_for_test(client: AsyncClient, policy_id: str, model_settings_id: str, name: str = "Test Camera For MS Deletion Test"):
    camera_payload = {
        "name": name,
        "url": "rtsp://example.com/ms_delete_test",
        "policy_id": policy_id,
        "model_settings_id": model_settings_id
    }
    response = await client.post("/configs/cameras", json=camera_payload)
    assert response.status_code == 201, f"Failed to create camera: {response.text}"
    return response.json()


@pytest.mark.asyncio
async def test_unauthenticated_access_to_model_settings_endpoints(async_client: AsyncClient):
    """Test that unauthenticated access to model settings endpoints returns 401."""
    ms_payload = {"name": "Auth Test MS", "model_path": "/m.pt", "confidence_threshold": 0.1, "iou_threshold": 0.1}
    
    response = await async_client.post("/configs/model_settings", json=ms_payload)
    assert response.status_code == 403

    response = await async_client.get("/configs/model_settings")
    assert response.status_code == 403

    response = await async_client.get("/configs/model_settings/some_ms_id")
    assert response.status_code == 403

    response = await async_client.put("/configs/model_settings/some_ms_id", json=ms_payload)
    assert response.status_code == 403

    response = await async_client.delete("/configs/model_settings/some_ms_id")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_model_settings_success(authenticated_async_client: AsyncClient):
    """Test successful model settings creation."""
    ms_payload = {
        "name": "YOLOv8 Large",
        "model_path": "/models/yolov8l.pt",
        "confidence_threshold": 0.6,
        "iou_threshold": 0.5,
        "other_params": {"resolution": "1280x720", "device": "cuda:0"}
    }
    response = await authenticated_async_client.post("/configs/model_settings", json=ms_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == ms_payload["name"]
    assert data["model_path"] == ms_payload["model_path"]
    assert data["confidence_threshold"] == ms_payload["confidence_threshold"]
    assert data["iou_threshold"] == ms_payload["iou_threshold"]
    assert data["other_params"] == ms_payload["other_params"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_model_settings_minimal_success(authenticated_async_client: AsyncClient):
    """Test successful model settings creation with only required fields."""
    ms_payload = {
        "name": "YOLOv8 Small",
        "model_path": "/models/yolov8s.pt",
        "confidence_threshold": 0.4,
        "iou_threshold": 0.3
    }
    response = await authenticated_async_client.post("/configs/model_settings", json=ms_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == ms_payload["name"]
    assert data["other_params"] is None # Check default for optional field
    assert "id" in data


@pytest.mark.asyncio
async def test_create_model_settings_missing_fields(authenticated_async_client: AsyncClient):
    """Test model settings creation with missing required fields."""
    required_fields = ["name", "model_path", "confidence_threshold", "iou_threshold"]
    base_payload = {
        "name": "Test Missing", "model_path": "/m.pt", "confidence_threshold": 0.1, "iou_threshold": 0.1
    }
    for field in required_fields:
        payload_copy = base_payload.copy()
        del payload_copy[field]
        response = await authenticated_async_client.post("/configs/model_settings", json=payload_copy)
        assert response.status_code == 422, f"Failed for missing field: {field}"

@pytest.mark.asyncio
async def test_create_model_settings_invalid_data_types(authenticated_async_client: AsyncClient):
    """Test model settings creation with invalid data types."""
    # Confidence threshold not a float
    response = await authenticated_async_client.post("/configs/model_settings", json={
        "name": "Invalid Conf MS", "model_path": "/m.pt", "confidence_threshold": "not_a_float", "iou_threshold": 0.1
    })
    assert response.status_code == 422

    # Name not a string
    response = await authenticated_async_client.post("/configs/model_settings", json={
        "name": 12345, "model_path": "/m.pt", "confidence_threshold": 0.1, "iou_threshold": 0.1
    })
    assert response.status_code == 422
    
    # other_params not a dictionary (if provided)
    response = await authenticated_async_client.post("/configs/model_settings", json={
        "name": "Invalid OtherParams MS", "model_path": "/m.pt", "confidence_threshold": 0.1, "iou_threshold": 0.1,
        "other_params": "not_a_dictionary"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_list_model_settings_with_items(authenticated_async_client: AsyncClient):
    """Test retrieving a list of model settings after creating one."""
    ms = await create_model_settings_for_test(authenticated_async_client, name="MS For Listing")

    response = await authenticated_async_client.get("/configs/model_settings")
    assert response.status_code == 200
    ms_list = response.json()
    assert len(ms_list) >= 1
    assert any(m["name"] == ms["name"] for m in ms_list)

@pytest.mark.asyncio
async def test_get_specific_model_settings_success(authenticated_async_client: AsyncClient):
    """Test retrieving existing model settings by ID."""
    created_ms = await create_model_settings_for_test(authenticated_async_client, name="Specific MS")
    created_ms_id = created_ms["id"]

    response = await authenticated_async_client.get(f"/configs/model_settings/{created_ms_id}")
    assert response.status_code == 200
    ms_data = response.json()
    assert ms_data["id"] == created_ms_id
    assert ms_data["name"] == "Specific MS"

@pytest.mark.asyncio
async def test_get_specific_model_settings_not_found(authenticated_async_client: AsyncClient):
    """Test retrieving non-existent model settings by ID."""
    response = await authenticated_async_client.get("/configs/model_settings/non_existent_ms_id_ABC")
    assert response.status_code == 404
    assert "ModelSettings not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_model_settings_success(authenticated_async_client: AsyncClient):
    """Test successful update of existing model settings."""
    created_ms = await create_model_settings_for_test(authenticated_async_client, name="MS To Update")
    created_ms_id = created_ms["id"]

    update_payload = {
        "name": "Updated MS Name",
        "model_path": "/models/updated.pt",
        "confidence_threshold": 0.75,
        "iou_threshold": 0.55,
        "other_params": {"new_key": "new_value"}
    }
    response = await authenticated_async_client.put(f"/configs/model_settings/{created_ms_id}", json=update_payload)
    assert response.status_code == 200
    updated_ms = response.json()
    assert updated_ms["id"] == created_ms_id
    assert updated_ms["name"] == update_payload["name"]
    assert updated_ms["model_path"] == update_payload["model_path"]
    assert updated_ms["confidence_threshold"] == update_payload["confidence_threshold"]
    assert updated_ms["iou_threshold"] == update_payload["iou_threshold"]
    assert updated_ms["other_params"] == update_payload["other_params"]

@pytest.mark.asyncio
async def test_update_model_settings_not_found(authenticated_async_client: AsyncClient):
    """Test updating non-existent model settings."""
    update_payload = {"name": "Non Existent MS Update", "model_path":"/n.pt", "confidence_threshold":0.1, "iou_threshold":0.1}
    response = await authenticated_async_client.put("/configs/model_settings/non_existent_ms_id_123", json=update_payload)
    assert response.status_code == 404
    assert "ModelSettings not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_model_settings_missing_fields(authenticated_async_client: AsyncClient):
    """Test updating model settings with missing required fields."""
    created_ms = await create_model_settings_for_test(authenticated_async_client, name="MS For Field Validation")
    created_ms_id = created_ms["id"]

    response = await authenticated_async_client.put(f"/configs/model_settings/{created_ms_id}", json={"name": None})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_model_settings_invalid_data_types(authenticated_async_client: AsyncClient):
    """Test updating model settings with invalid data types."""
    created_ms = await create_model_settings_for_test(authenticated_async_client, name="MS For Type Validation")
    created_ms_id = created_ms["id"]

    response = await authenticated_async_client.put(f"/configs/model_settings/{created_ms_id}", json={
        "name": "Valid Name", "model_path": "/valid.pt", "confidence_threshold": "not_a_float_again", "iou_threshold": 0.1
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_model_settings_id_mismatch(authenticated_async_client: AsyncClient):
    """Test that model_settings ID in path cannot be changed by ID in body."""
    created_ms = await create_model_settings_for_test(authenticated_async_client, "MS ID Mismatch Test")
    created_ms_id = created_ms["id"]

    update_payload_with_different_id = {
        "id": "completely_different_ms_id_789",
        "name": "Attempting MS ID Change",
        "model_path": created_ms["model_path"],
        "confidence_threshold": created_ms["confidence_threshold"],
        "iou_threshold": created_ms["iou_threshold"]
    }
    response = await authenticated_async_client.put(
        f"/configs/model_settings/{created_ms_id}",
        json=update_payload_with_different_id
    )
    assert response.status_code == 400
    assert "ModelSettings ID in path does not match ID in body" in response.json()["detail"]

    get_response = await authenticated_async_client.get(f"/configs/model_settings/{created_ms_id}")
    assert get_response.json()["name"] == "MS ID Mismatch Test" # Name should not have changed

@pytest.mark.asyncio
async def test_delete_model_settings_success(authenticated_async_client: AsyncClient):
    """Test successful deletion of existing model settings."""
    created_ms = await create_model_settings_for_test(authenticated_async_client, name="MS To Be Deleted")
    created_ms_id = created_ms["id"]

    delete_response = await authenticated_async_client.delete(f"/configs/model_settings/{created_ms_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "ModelSettings deleted successfully"}

    get_response = await authenticated_async_client.get(f"/configs/model_settings/{created_ms_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_model_settings_not_found(authenticated_async_client: AsyncClient):
    """Test deleting non-existent model settings."""
    response = await authenticated_async_client.delete("/configs/model_settings/non_existent_ms_id_404")
    assert response.status_code == 404
    assert "ModelSettings not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_model_settings_associated_with_camera(authenticated_async_client: AsyncClient):
    """Test deleting model settings that are currently associated with a CameraConfig."""
    # 1. Create ModelSettings
    ms_to_delete = await create_model_settings_for_test(authenticated_async_client, name="InUseMS")
    ms_id = ms_to_delete["id"]

    # 2. Create Policy (prerequisite for CameraConfig)
    policy = await create_policy_for_test(authenticated_async_client)
    policy_id = policy["id"]

    # 3. Create a CameraConfig that uses the model settings
    await create_camera_for_test(authenticated_async_client, policy_id, ms_id)

    # 4. Attempt to delete the model settings
    delete_response = await authenticated_async_client.delete(f"/configs/model_settings/{ms_id}")
    
    # Current API behavior: Allows deletion (200 OK)
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "ModelSettings deleted successfully"}

    # Verify model settings are actually deleted
    get_response = await authenticated_async_client.get(f"/configs/model_settings/{ms_id}")
    assert get_response.status_code == 404

    # TODO/Note for future: The API currently allows deleting model settings even if
    # associated with a camera configuration. This can lead to orphaned model_settings_id
    # references in the cameras table. Future improvements could include:
    # - Preventing deletion of in-use model settings (returning a 400/409 error).
    # - Implementing a soft delete.
    # - Setting the model_settings_id in associated cameras to null (if schema allows).
    print("Test Note: Verified that in-use model settings can be deleted. This is a potential area for future API improvement regarding referential integrity.")
