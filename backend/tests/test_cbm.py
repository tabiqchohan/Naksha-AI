import pytest
from app.models.cbm_schemas import (
    CanonicalBuildingModel,
    SiteGeometry,
    BuildingLevel,
    WallSegment,
    RoomPolygon,
    Opening,
)
from app.models.schemas import FloorPlan, Plot, Room, Door, Window, MaterialEstimate
from app.services.cbm_adapter import CBMAdapter

def test_cbm_creation():
    site = SiteGeometry(plot_width=50.0, plot_length=60.0, unit="feet", marla_size=13.3, total_area_sqft=3000.0)
    level0 = BuildingLevel(level_id="lvl_0", index=0, name="Ground Floor", elevation=0.0, height=11.0)
    wall1 = WallSegment(id="w1", level_id="lvl_0", start=(0, 0), end=(50, 0), thickness=0.75, wall_type="exterior")
    room1 = RoomPolygon(id="r1", level_id="lvl_0", name="Master Bed", room_type="master_bedroom", polygon=[(0,0), (18,0), (18,16), (0,16)], area_sqft=288.0)
    opening1 = Opening(id="op1", wall_id="w1", level_id="lvl_0", opening_type="door", offset_from_start=5.0, width=3.5)

    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id="test_proj_1",
        title="Test Villa",
        site=site,
        levels=[level0],
        walls=[wall1],
        rooms=[room1],
        openings=[opening1],
    )

    assert cbm.project_id == "test_proj_1"
    assert len(cbm.rooms) == 1
    assert cbm.rooms[0].area_sqft == 288.0
    assert cbm.openings[0].wall_id == "w1"

def test_cbm_serialization():
    site = SiteGeometry(plot_width=25.0, plot_length=45.0, unit="feet", marla_size=5.0, total_area_sqft=1125.0)
    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id="test_5marla",
        title="5 Marla House",
        site=site,
        levels=[BuildingLevel(level_id="lvl_0", index=0, name="Ground", elevation=0.0, height=11.0)]
    )
    data = cbm.model_dump()
    reconstructed = CanonicalBuildingModel(**data)
    assert reconstructed.project_id == "test_5marla"
    assert reconstructed.site.plot_width == 25.0

def test_legacy_adapter_conversion():
    plot = Plot(width=50.0, length=60.0, unit="feet", marla_size=13.3, total_area_sqft=3000.0)
    room = Room(id="r_1", name="LIVING ROOM", type="living_room", x=0, y=0, width=20, length=20, sqft=400, floor_level=0)
    door = Door(id="d_1", room_name="LIVING ROOM", wall="north", position=5.0, width=3.5)
    window = Window(id="w_1", room_name="LIVING ROOM", wall="east", position=4.0, width=4.0)

    legacy_plan = FloorPlan(
        id="legacy_123",
        title="Legacy Plan",
        plot=plot,
        rooms=[room],
        doors=[door],
        windows=[window],
    )

    # Convert to CBM
    cbm = CBMAdapter.to_cbm(legacy_plan)
    assert cbm.project_id == "legacy_123"
    assert len(cbm.rooms) == 1
    assert len(cbm.openings) == 2

    # Convert back to legacy FloorPlan
    roundtrip_plan = CBMAdapter.from_cbm(cbm)
    assert roundtrip_plan.id == "legacy_123"
    assert len(roundtrip_plan.rooms) == 1
    assert roundtrip_plan.rooms[0].name == "LIVING ROOM"

def test_cbm_validation_errors():
    site = SiteGeometry(plot_width=50.0, plot_length=60.0, unit="feet")
    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id="val_test",
        title="Validation Test",
        site=site,
        levels=[BuildingLevel(level_id="lvl_0", index=0, name="Ground", elevation=0, height=11)],
        openings=[Opening(id="op1", wall_id="non_existent_wall", level_id="lvl_0", opening_type="door", offset_from_start=2, width=3.5)],
        rooms=[RoomPolygon(id="r1", level_id="invalid_lvl", name="Bed", room_type="bedroom", polygon=[(0,0),(10,0),(10,10),(0,10)], area_sqft=100)]
    )

    errors = CBMAdapter.validate_cbm(cbm)
    assert len(errors) >= 2
    assert any("non_existent_wall" in err for err in errors)
    assert any("invalid_lvl" in err for err in errors)

@pytest.mark.parametrize("plot_name,w,l,marla", [
    ("3 Marla", 20.0, 35.0, 3.0),
    ("5 Marla", 25.0, 45.0, 5.0),
    ("7 Marla", 30.0, 55.0, 7.0),
    ("10 Marla", 35.0, 65.0, 10.0),
    ("1 Kanal", 50.0, 90.0, 20.0),
])
def test_plot_fixtures(plot_name, w, l, marla):
    site = SiteGeometry(plot_width=w, plot_length=l, unit="feet", marla_size=marla, total_area_sqft=w*l)
    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id=f"fixture_{marla}",
        title=f"{plot_name} House",
        site=site,
        levels=[BuildingLevel(level_id="lvl_0", index=0, name="Ground", elevation=0.0, height=11.0)],
    )
    assert cbm.site.plot_width == w
    assert cbm.site.plot_length == l
    assert cbm.site.marla_size == marla
