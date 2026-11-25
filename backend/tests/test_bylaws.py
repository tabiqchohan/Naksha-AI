import pytest
from app.models.schemas import FloorPlan, Plot, Room
from app.services.cbm_adapter import CBMAdapter
from app.services.bylaws_engine import BylawsEngine

@pytest.fixture
def sample_cbm():
    plot = Plot(width=25.0, length=45.0, unit="feet", marla_size=5.0, total_area_sqft=1125.0)
    rooms = [
        Room(id="r1", name="Living Room", type="living_room", x=0, y=0, width=25, length=20, sqft=500.0, floor_level=0),
        Room(id="r2", name="Kitchen", type="kitchen", x=0, y=20, width=12, length=10, sqft=120.0, floor_level=0)
    ]
    fp = FloorPlan(
        id="proj_bylaws_test",
        title="5 Marla Bylaws Residence",
        description="Test plan for Phase 7 bylaws evaluation",
        plot=plot,
        rooms=rooms
    )
    return CBMAdapter.to_cbm(fp)

def test_bylaws_packs():
    packs = BylawsEngine.packs()
    assert len(packs) >= 5
    assert any(p["id"] == "dha_lahore" for p in packs)
    assert any(p["id"] == "pakistan_generic" for p in packs)

def test_bylaws_evaluate_cbm(sample_cbm):
    report = BylawsEngine.evaluate_cbm(sample_cbm, "pakistan_generic")
    assert report["project_id"] == "proj_bylaws_test"
    assert "checks" in report
    assert len(report["checks"]) >= 4

def test_bylaws_compliance_api(client, user, sample_cbm):
    payload = {
        "cbm": sample_cbm.dict(),
        "pack_id": "dha_lahore"
    }
    resp = client.post("/api/v1/plans/cbm-compliance", json=payload, headers=user["headers"])
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert "compliance_report" in data
    assert data["compliance_report"]["pack_id"] == "dha_lahore"

def test_bylaws_compliance_unauthenticated(client, sample_cbm):
    payload = {
        "cbm": sample_cbm.dict(),
        "pack_id": "pakistan_generic"
    }
    resp = client.post("/api/v1/plans/cbm-compliance", json=payload)
    assert resp.status_code == 401
