import pytest
from app.models.schemas import FloorPlan, Plot, Room
from app.services.cbm_adapter import CBMAdapter
from app.services.geometry_validator import CBMGeometryValidator
from app.models.cbm_schemas import WallSegment

@pytest.fixture
def sample_cbm():
    plot = Plot(width=25.0, length=45.0, unit="feet", marla_size=5.0, total_area_sqft=1125.0)
    rooms = [
        Room(id="r1", name="Living Room", type="living_room", x=0, y=0, width=25, length=20, sqft=500.0, floor_level=0),
        Room(id="r2", name="Kitchen", type="kitchen", x=0, y=20, width=12, length=10, sqft=120.0, floor_level=0)
    ]
    fp = FloorPlan(
        id="proj_cbm_editor",
        title="CBM Editor Test Plan",
        description="Test plan for 2D CBM editor updates",
        plot=plot,
        rooms=rooms
    )
    return CBMAdapter.to_cbm(fp)

def test_cbm_update_endpoint(client, user, sample_cbm):
    cbm_dict = sample_cbm.dict()
    cbm_dict["rooms"][0]["area_sqft"] = 550.0

    resp = client.post("/api/v1/plans/cbm-update", json=cbm_dict, headers=user["headers"])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert data["cbm"]["rooms"][0]["area_sqft"] == 550.0
    assert "floor_plan" in data
    assert "material_estimate" in data
    assert data["material_estimate"]["estimated_cost_pkr"] > 0

def test_cbm_update_unauthenticated(client, sample_cbm):
    cbm_dict = sample_cbm.dict()
    resp = client.post("/api/v1/plans/cbm-update", json=cbm_dict)
    assert resp.status_code == 401

def test_wall_drawing_and_deduplication():
    w1 = WallSegment(id="w1", level_id="lvl_0", start=(0, 0), end=(10, 0), thickness=0.75, wall_type="exterior")
    w2 = WallSegment(id="w2", level_id="lvl_0", start=(10, 0), end=(0, 0), thickness=0.75, wall_type="exterior") # Reversed
    deduped = CBMGeometryValidator.deduplicate_walls([w1, w2])
    assert len(deduped) == 1

def test_room_creation_polygon_validation():
    valid_poly = [(0, 0), (10, 0), (10, 10), (0, 10)]
    is_valid, msg, area = CBMGeometryValidator.validate_polygon_geometry(valid_poly)
    assert is_valid is True
    assert area == 100.0

    # Self-intersecting bowtie polygon
    invalid_poly = [(0, 0), (10, 10), (0, 10), (10, 0)]
    is_valid_inv, msg_inv, _ = CBMGeometryValidator.validate_polygon_geometry(invalid_poly)
    assert is_valid_inv is False
