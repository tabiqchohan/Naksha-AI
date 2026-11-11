def test_project_crud(client, user):
    payload = {
        "title": "Test House",
        "building_type": "house",
        "floors": 1,
        "plot_width": 25,
        "plot_length": 45,
        "prompt": "test",
        "floor_plan_data": {"rooms": [], "plot": {"width": 25, "length": 45}},
    }
    saved = client.post("/api/v1/projects/save", json=payload, headers=user["headers"])
    assert saved.status_code == 200
    project_id = saved.json()["project_id"]

    listed = client.get("/api/v1/projects/list", headers=user["headers"])
    assert listed.status_code == 200
    assert any(item["project_id"] == project_id for item in listed.json())

    fetched = client.get(f"/api/v1/projects/{project_id}", headers=user["headers"])
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Test House"

    updated = client.put(
        f"/api/v1/projects/{project_id}",
        json={"title": "Updated House", "is_favorite": True},
        headers=user["headers"],
    )
    assert updated.status_code == 200

    fetched = client.get(f"/api/v1/projects/{project_id}", headers=user["headers"])
    assert fetched.json()["title"] == "Updated House"
    assert fetched.json()["is_favorite"] is True

    deleted = client.delete(f"/api/v1/projects/{project_id}", headers=user["headers"])
    assert deleted.status_code == 200
    assert client.get(f"/api/v1/projects/{project_id}", headers=user["headers"]).status_code == 404


def test_project_requires_auth(client):
    assert client.get("/api/v1/projects/list").status_code == 401
