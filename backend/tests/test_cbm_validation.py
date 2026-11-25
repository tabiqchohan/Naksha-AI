import pytest
from app.models.cbm_schemas import (
    CanonicalBuildingModel,
    SiteGeometry,
    BuildingLevel,
    WallSegment,
    RoomPolygon,
    Opening,
    StairFlight,
)
from app.services.geometry_validator import CBMGeometryValidator, CBMValidationPipeline
from app.services.cbm_adapter import CBMAdapter
from app.models.schemas import FloorPlan, Plot, Room, Door, Window

def test_valid_polygon_geometry():
    # Valid rectangle polygon
    poly = [(0, 0), (15, 0), (15, 12), (0, 12)]
    valid, err, area = CBMGeometryValidator.validate_polygon_geometry(poly)
    assert valid is True
    assert err == ""
    assert area == 180.0

def test_self_intersecting_polygon():
    # Bowtie self-intersecting polygon
    poly = [(0, 0), (10, 10), (0, 10), (10, 0)]
    valid, err, area = CBMGeometryValidator.validate_polygon_geometry(poly)
    assert valid is False
    assert "self-intersecting" in err.lower() or "invalid" in err.lower()

def test_zero_area_polygon():
    poly = [(0, 0), (5, 0), (5, 0)]
    valid, err, area = CBMGeometryValidator.validate_polygon_geometry(poly)
    assert valid is False

def test_wall_deduplication():
    walls = [
        WallSegment(id="w1", level_id="lvl_0", start=(0, 0), end=(50, 0), wall_type="interior"),
        WallSegment(id="w2", level_id="lvl_0", start=(0, 0), end=(50, 0), wall_type="exterior"),  # duplicate, should prefer exterior
        WallSegment(id="w3", level_id="lvl_0", start=(0, 0), end=(0, 60), wall_type="exterior"),
    ]
    deduped = CBMGeometryValidator.deduplicate_walls(walls)
    assert len(deduped) == 2
    # Check that w2 (exterior) replaced w1 on (0,0)-(50,0)
    w_bottom = next(w for w in deduped if w.start == (0, 0) and w.end == (50, 0))
    assert w_bottom.wall_type == "exterior"

def test_room_overlap_detection():
    rooms = [
        RoomPolygon(id="r1", level_id="lvl_0", name="Room A", room_type="bedroom", polygon=[(0, 0), (20, 0), (20, 20), (0, 20)], area_sqft=400.0),
        RoomPolygon(id="r2", level_id="lvl_0", name="Room B", room_type="kitchen", polygon=[(10, 10), (30, 10), (30, 30), (10, 30)], area_sqft=400.0),
    ]
    errors = CBMGeometryValidator.detect_room_overlaps(rooms)
    assert len(errors) == 1
    assert "Room overlap detected" in errors[0]

def test_opening_boundary_validation():
    walls = [
        WallSegment(id="w1", level_id="lvl_0", start=(0, 0), end=(20, 0), wall_type="exterior")
    ]
    levels = [
        BuildingLevel(level_id="lvl_0", index=0, name="Ground", elevation=0, height=11)
    ]
    # Valid opening
    valid_openings = [
        Opening(id="op1", wall_id="w1", level_id="lvl_0", opening_type="door", offset_from_start=5.0, width=3.5)
    ]
    errs = CBMGeometryValidator.validate_openings(valid_openings, walls, levels)
    assert len(errs) == 0

    # Invalid opening exceeding wall length (Wall length is 20, offset 18 + width 5 = 23)
    invalid_openings = [
        Opening(id="op2", wall_id="w1", level_id="lvl_0", opening_type="door", offset_from_start=18.0, width=5.0)
    ]
    errs2 = CBMGeometryValidator.validate_openings(invalid_openings, walls, levels)
    assert len(errs2) == 1
    assert "exceeds host wall" in errs2[0]

def test_complete_validation_pipeline():
    site = SiteGeometry(plot_width=50.0, plot_length=60.0, unit="feet", total_area_sqft=3000.0)
    level0 = BuildingLevel(level_id="lvl_0", index=0, name="Ground Floor", elevation=0.0, height=11.0)
    wall1 = WallSegment(id="w1", level_id="lvl_0", start=(0, 0), end=(20, 0), wall_type="exterior")
    room1 = RoomPolygon(id="r1", level_id="lvl_0", name="Master Bed", room_type="master_bedroom", polygon=[(0, 0), (18, 0), (18, 16), (0, 16)], area_sqft=288.0)
    opening1 = Opening(id="op1", wall_id="w1", level_id="lvl_0", opening_type="door", offset_from_start=2.0, width=3.5)

    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id="test_pipeline_proj",
        title="Valid Test House",
        site=site,
        levels=[level0],
        walls=[wall1],
        rooms=[room1],
        openings=[opening1],
    )

    result = CBMValidationPipeline.run_validation(cbm)
    assert result.is_valid is True
    assert result.score > 80.0
    assert len(result.errors) == 0

def test_invalid_pipeline_detection():
    site = SiteGeometry(plot_width=30.0, plot_length=40.0, unit="feet")
    level0 = BuildingLevel(level_id="lvl_0", index=0, name="Ground", elevation=0, height=11)
    # Self-intersecting room polygon
    room_bad = RoomPolygon(id="r_bad", level_id="lvl_0", name="Bad Room", room_type="bedroom", polygon=[(0, 0), (10, 10), (0, 10), (10, 0)], area_sqft=100.0)
    # Opening referencing non-existent wall
    op_bad = Opening(id="op_bad", wall_id="non_existent", level_id="lvl_0", opening_type="door", offset_from_start=0, width=3.5)

    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id="test_invalid_proj",
        title="Invalid House",
        site=site,
        levels=[level0],
        rooms=[room_bad],
        openings=[op_bad],
    )

    result = CBMValidationPipeline.run_validation(cbm)
    assert result.is_valid is False
    assert len(result.errors) >= 2
