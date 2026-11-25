import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.schemas import FloorPlan, Plot, Room, Door, Window
from app.services.cbm_adapter import CBMAdapter
from app.services.architectural_drawing_service import ArchitecturalDrawingService

client = TestClient(app)

@pytest.fixture
def sample_floor_plan():
    plot = Plot(width=25.0, length=45.0, unit="feet", marla_size=5.0, total_area_sqft=1125.0)
    rooms = [
        Room(id="r1", name="Living Room", type="living_room", x=0, y=0, width=25, length=20, sqft=500.0, floor_level=0),
        Room(id="r2", name="Kitchen", type="kitchen", x=0, y=20, width=12, length=10, sqft=120.0, floor_level=0),
        Room(id="r3", name="Bed 1", type="bedroom", x=12, y=20, width=13, length=15, sqft=195.0, floor_level=1),
        Room(id="r4", name="Bath 1", type="attached_bath", x=12, y=35, width=13, length=10, sqft=130.0, floor_level=1),
    ]
    doors = [
        Door(id="d1", room_name="Living Room", wall="south", position=5.0, width=3.5, swing="inward_left"),
        Door(id="d2", room_name="Bed 1", wall="north", position=2.0, width=3.0, swing="inward_right"),
    ]
    windows = [
        Window(id="w1", room_name="Living Room", wall="west", position=4.0, width=4.0),
        Window(id="w2", room_name="Bed 1", wall="east", position=3.0, width=4.0),
    ]
    return FloorPlan(
        id="proj_arch_test",
        title="5 Marla Coordinated Residence",
        description="Test plan for Phase 4 architectural drawings",
        plot=plot,
        rooms=rooms,
        doors=doors,
        windows=windows,
    )

def test_cbm_adapter_conversion(sample_floor_plan):
    cbm = CBMAdapter.to_cbm(sample_floor_plan)
    assert cbm.project_id == "proj_arch_test"
    assert len(cbm.levels) == 2
    assert len(cbm.rooms) == 4
    assert len(cbm.walls) > 0

    back_plan = CBMAdapter.from_cbm(cbm)
    assert back_plan.id == "proj_arch_test"
    assert len(back_plan.rooms) == 4

def test_architectural_drawings_payload(sample_floor_plan):
    cbm = CBMAdapter.to_cbm(sample_floor_plan)
    payload = ArchitecturalDrawingService.generate_drawings_payload(cbm)

    assert payload["project_id"] == "proj_arch_test"
    assert len(payload["levels"]) == 2
    assert payload["site"]["plot_width"] == 25.0
    assert payload["site"]["plot_length"] == 45.0
    assert len(payload["schedules"]["doors"]) == 2
    assert len(payload["schedules"]["windows"]) == 2
    assert payload["schedules"]["total_building_area_sqft"] > 0

    # Verify orthographic elevations & sections exist in payload
    assert "front" in payload["elevations"]
    assert "rear" in payload["elevations"]
    assert "left" in payload["elevations"]
    assert "right" in payload["elevations"]
    assert "longitudinal_section_aa" in payload["sections"]
    assert "transverse_section_bb" in payload["sections"]

def test_architectural_pdf_generation(sample_floor_plan):
    cbm = CBMAdapter.to_cbm(sample_floor_plan)
    pdf_bytes = ArchitecturalDrawingService.generate_architectural_pdf(cbm, add_watermark=True)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

def test_architectural_dxf_generation(sample_floor_plan):
    cbm = CBMAdapter.to_cbm(sample_floor_plan)
    dxf_bytes = ArchitecturalDrawingService.generate_dxf(cbm, add_watermark=True)
    assert isinstance(dxf_bytes, bytes)
    assert len(dxf_bytes) > 100

def test_unauthenticated_drawing_requests(sample_floor_plan):
    # Unauthenticated requests should be rejected with 401
    res1 = client.post("/api/v1/plans/cbm-drawings", json=sample_floor_plan.model_dump())
    assert res1.status_code == 401

    res2 = client.post("/api/v1/plans/cbm-export-pdf", json=sample_floor_plan.model_dump())
    assert res2.status_code == 401

    res3 = client.post("/api/v1/plans/cbm-export-dxf", json=sample_floor_plan.model_dump())
    assert res3.status_code == 401

def test_authenticated_drawing_requests(client, user, sample_floor_plan):
    # Authenticated requests should succeed with 200
    res1 = client.post("/api/v1/plans/cbm-drawings", json=sample_floor_plan.model_dump(), headers=user["headers"])
    assert res1.status_code == 200
    assert res1.json()["status"] in ["success", "warning"]

    res2 = client.post("/api/v1/plans/cbm-export-pdf", json=sample_floor_plan.model_dump(), headers=user["headers"])
    assert res2.status_code == 200
    assert res2.headers["content-type"] == "application/pdf"
    assert len(res2.content) > 1000

    res3 = client.post("/api/v1/plans/cbm-export-dxf", json=sample_floor_plan.model_dump(), headers=user["headers"])
    assert res3.status_code == 200
    assert res3.headers["content-type"] == "application/dxf"
    assert len(res3.content) > 100
