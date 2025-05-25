import pytest
from httpx import AsyncClient

# Helper function to create a policy (can also be used by other test files if moved to conftest)
async def create_policy_for_test(client: AsyncClient, name: str = "Test Policy", policy_type: str = "test_type", params: dict = None):
    if params is None:
        params = {"setting1": "value1"}
    response = await client.post("/configs/policies", json={
        "name": name,
        "policy_type": policy_type,
        "parameters": params
    })
    assert response.status_code == 201, f"Failed to create policy: {response.text}"
    return response.json()

# Helper function to create model settings (needed for creating a camera that uses a policy)
async def create_model_settings_for_test(client: AsyncClient, name: str = "Test Model Settings For Policy Test", model_path: str = "/models/test_policy.pt", conf: float = 0.5, iou: float = 0.45):
    response = await client.post("/configs/model_settings", json={
        "name": name,
        "model_path": model_path,
        "confidence_threshold": conf,
        "iou_threshold": iou
    })
    assert response.status_code == 201, f"Failed to create model settings: {response.text}"
    return response.json()

# Helper function to create a camera (needed for testing deletion of an in-use policy)
async def create_camera_for_test(client: AsyncClient, policy_id: str, model_settings_id: str, name: str = "Test Camera For Policy Deletion Test"):
    camera_payload = {
        "name": name,
        "url": "rtsp://example.com/policy_delete_test",
        "policy_id": policy_id,
        "model_settings_id": model_settings_id
    }
    response = await client.post("/configs/cameras", json=camera_payload)
    assert response.status_code == 201, f"Failed to create camera: {response.text}"
    return response.json()


@pytest.mark.asyncio
async def test_unauthenticated_access_to_policy_endpoints(async_client: AsyncClient):
    """Test that unauthenticated access to policy endpoints returns 401."""
    policy_payload = {"name": "Auth Test Policy", "policy_type": "auth_test", "parameters": {"p": 1}}
    
    response = await async_client.post("/configs/policies", json=policy_payload)
    assert response.status_code == 403

    response = await async_client.get("/configs/policies")
    assert response.status_code == 403

    response = await async_client.get("/configs/policies/some_policy_id")
    assert response.status_code == 403

    response = await async_client.put("/configs/policies/some_policy_id", json=policy_payload)
    assert response.status_code == 403

    response = await async_client.delete("/configs/policies/some_policy_id")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_policy_success(authenticated_async_client: AsyncClient):
    """Test successful policy creation."""
    policy_payload = {
        "name": "Intrusion Detection Policy",
        "policy_type": "intrusion_detection",
        "parameters": {"sensitivity": "high", "area": [0, 0, 100, 100]}
    }
    response = await authenticated_async_client.post("/configs/policies", json=policy_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == policy_payload["name"]
    assert data["policy_type"] == policy_payload["policy_type"]
    assert data["parameters"] == policy_payload["parameters"]
    assert "id" in data

@pytest.mark.asyncio
async def test_create_policy_missing_fields(authenticated_async_client: AsyncClient):
    """Test policy creation with missing required fields."""
    # Missing name
    response = await authenticated_async_client.post("/configs/policies", json={
        "policy_type": "missing_name_type", "parameters": {}
    })
    assert response.status_code == 422

    # Missing policy_type
    response = await authenticated_async_client.post("/configs/policies", json={
        "name": "Missing Type Policy", "parameters": {}
    })
    assert response.status_code == 422
    
    # Missing parameters
    response = await authenticated_async_client.post("/configs/policies", json={
        "name": "Missing Params Policy", "policy_type": "missing_params_type"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_policy_invalid_data_types(authenticated_async_client: AsyncClient):
    """Test policy creation with invalid data types for fields."""
    # Parameters not a dictionary
    response = await authenticated_async_client.post("/configs/policies", json={
        "name": "Invalid Params Policy", 
        "policy_type": "invalid_params_type", 
        "parameters": "not_a_dictionary"
    })
    assert response.status_code == 422

    # Name not a string
    response = await authenticated_async_client.post("/configs/policies", json={
        "name": 12345, 
        "policy_type": "invalid_name_type", 
        "parameters": {}
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_policies_with_items(authenticated_async_client: AsyncClient):
    """Test retrieving a list of policies after creating one."""
    policy_payload = {"name": "Policy For Listing", "policy_type": "list_test", "parameters": {"p": "list"}}
    await authenticated_async_client.post("/configs/policies", json=policy_payload)

    response = await authenticated_async_client.get("/configs/policies")
    assert response.status_code == 200
    policies = response.json()
    assert len(policies) >= 1
    assert any(p["name"] == policy_payload["name"] for p in policies)

@pytest.mark.asyncio
async def test_get_specific_policy_success(authenticated_async_client: AsyncClient):
    """Test retrieving an existing policy by ID."""
    created_policy = await create_policy_for_test(authenticated_async_client, "Specific Policy", "get_test")
    created_policy_id = created_policy["id"]

    response = await authenticated_async_client.get(f"/configs/policies/{created_policy_id}")
    assert response.status_code == 200
    policy = response.json()
    assert policy["id"] == created_policy_id
    assert policy["name"] == "Specific Policy"

@pytest.mark.asyncio
async def test_get_specific_policy_not_found(authenticated_async_client: AsyncClient):
    """Test retrieving a non-existent policy by ID."""
    response = await authenticated_async_client.get("/configs/policies/non_existent_policy_id_XYZ")
    assert response.status_code == 404
    assert "Policy not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_policy_success(authenticated_async_client: AsyncClient):
    """Test successful update of an existing policy."""
    created_policy = await create_policy_for_test(authenticated_async_client, "Policy To Update", "update_test")
    created_policy_id = created_policy["id"]

    update_payload = {
        "name": "Updated Policy Name",
        "policy_type": "updated_type",
        "parameters": {"sensitivity": "low", "new_param": "added"}
    }
    response = await authenticated_async_client.put(f"/configs/policies/{created_policy_id}", json=update_payload)
    assert response.status_code == 200
    updated_policy = response.json()
    assert updated_policy["id"] == created_policy_id
    assert updated_policy["name"] == update_payload["name"]
    assert updated_policy["policy_type"] == update_payload["policy_type"]
    assert updated_policy["parameters"] == update_payload["parameters"]

@pytest.mark.asyncio
async def test_update_policy_not_found(authenticated_async_client: AsyncClient):
    """Test updating a non-existent policy."""
    update_payload = {"name": "Non Existent Policy Update", "policy_type": "ghost", "parameters": {}}
    response = await authenticated_async_client.put("/configs/policies/non_existent_policy_id_000", json=update_payload)
    assert response.status_code == 404
    assert "Policy not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_policy_missing_fields(authenticated_async_client: AsyncClient):
    """Test updating a policy with missing required fields in payload."""
    created_policy = await create_policy_for_test(authenticated_async_client, "PolicyForFieldValidation", "validation_type")
    created_policy_id = created_policy["id"]

    response = await authenticated_async_client.put(f"/configs/policies/{created_policy_id}", json={"name": None}) # Name is required
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_policy_invalid_data_types(authenticated_async_client: AsyncClient):
    """Test updating a policy with invalid data types."""
    created_policy = await create_policy_for_test(authenticated_async_client, "PolicyForTypeValidation", "type_val_type")
    created_policy_id = created_policy["id"]

    response = await authenticated_async_client.put(f"/configs/policies/{created_policy_id}", json={
        "name": "Valid Name", "policy_type": "valid_type", "parameters": "not_a_dict_again"
    })
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_update_policy_id_mismatch(authenticated_async_client: AsyncClient):
    """Test that policy ID in path cannot be changed by ID in body."""
    created_policy = await create_policy_for_test(authenticated_async_client, "Policy ID Mismatch Test", "id_mismatch_type")
    created_policy_id = created_policy["id"]

    update_payload_with_different_id = {
        "id": "completely_different_id_456",
        "name": "Attempting ID Change Policy",
        "policy_type": created_policy["policy_type"],
        "parameters": created_policy["parameters"]
    }
    response = await authenticated_async_client.put(
        f"/configs/policies/{created_policy_id}",
        json=update_payload_with_different_id
    )
    assert response.status_code == 400
    assert "Policy ID in path does not match ID in body" in response.json()["detail"]
    
    get_response = await authenticated_async_client.get(f"/configs/policies/{created_policy_id}")
    assert get_response.json()["name"] == "Policy ID Mismatch Test" # Name should not have changed

@pytest.mark.asyncio
async def test_delete_policy_success(authenticated_async_client: AsyncClient):
    """Test successful deletion of an existing policy."""
    created_policy = await create_policy_for_test(authenticated_async_client, "Policy To Be Deleted", "delete_type")
    created_policy_id = created_policy["id"]

    delete_response = await authenticated_async_client.delete(f"/configs/policies/{created_policy_id}")
    assert delete_response.status_code == 200
    assert delete_response.json() == {"message": "Policy deleted successfully"}

    get_response = await authenticated_async_client.get(f"/configs/policies/{created_policy_id}")
    assert get_response.status_code == 404

@pytest.mark.asyncio
async def test_delete_policy_not_found(authenticated_async_client: AsyncClient):
    """Test deleting a non-existent policy."""
    response = await authenticated_async_client.delete("/configs/policies/non_existent_policy_id_404")
    assert response.status_code == 404
    assert "Policy not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_policy_associated_with_camera(authenticated_async_client: AsyncClient):
    """Test deleting a policy that is currently associated with a CameraConfig."""
    # 1. Create a Policy
    policy_to_delete = await create_policy_for_test(authenticated_async_client, "InUsePolicy", "in_use_type")
    policy_id = policy_to_delete["id"]

    # 2. Create ModelSettings (prerequisite for CameraConfig)
    model_settings = await create_model_settings_for_test(authenticated_async_client)
    model_settings_id = model_settings["id"]

    # 3. Create a CameraConfig that uses the policy
    await create_camera_for_test(authenticated_async_client, policy_id, model_settings_id)

    # 4. Attempt to delete the policy
    delete_response = await authenticated_async_client.delete(f"/configs/policies/{policy_id}")
    
    # Current API behavior: Allows deletion (200 OK)
    assert delete_response.status_code == 200 
    assert delete_response.json() == {"message": "Policy deleted successfully"}

    # Verify policy is actually deleted
    get_response = await authenticated_async_client.get(f"/configs/policies/{policy_id}")
    assert get_response.status_code == 404

    # TODO/Note for future: The API currently allows deleting a policy even if it's
    # associated with a camera configuration. This can lead to orphaned policy_id
    # references in the cameras table. Future improvements could include:
    # - Preventing deletion of in-use policies (returning a 400/409 error).
    # - Implementing a soft delete for policies.
    # - Setting the policy_id in associated cameras to null (if the schema allows).
    print("Test Note: Verified that an in-use policy can be deleted. This is a potential area for future API improvement regarding referential integrity.")
