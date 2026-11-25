import pytest
from app.models.schemas import FloorPlan, Plot, Room
from app.services.cbm_adapter import CBMAdapter
from app.services.boq_service import BOQService

@pytest.fixture
def sample_cbm():
    plot = Plot(width=25.0, length=45.0, unit="feet", marla_size=5.0, total_area_sqft=1125.0)
    rooms = [
        Room(id="r1", name="Living Room", type="living_room", x=0, y=0, width=25, length=20, sqft=500.0, floor_level=0),
        Room(id="r2", name="Kitchen", type="kitchen", x=0, y=20, width=12, length=10, sqft=120.0, floor_level=0)
    ]
    fp = FloorPlan(
        id="proj_boq_test",
        title="5 Marla BOQ Residence",
        description="Test plan for Phase 6 BOQ estimation",
        plot=plot,
        rooms=rooms
    )
    return CBMAdapter.to_cbm(fp)

def test_boq_generation(sample_cbm):
    boq = BOQService.generate_boq(sample_cbm)
    assert boq["project_id"] == "proj_boq_test"
    assert boq["currency"] == "PKR"
    assert boq["estimated_total_pkr"] > 0
    assert len(boq["stages"]) >= 8
    assert boq["total_covered_area_sqft"] > 0

def test_boq_api_endpoint(client, user, sample_cbm):
    cbm_dict = sample_cbm.dict()
    resp = client.post("/api/v1/plans/cbm-boq", json=cbm_dict, headers=user["headers"])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert "boq" in data
    assert data["boq"]["estimated_total_pkr"] > 0
