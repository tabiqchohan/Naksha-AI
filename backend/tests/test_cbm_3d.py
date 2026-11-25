import pytest
from app.models.cbm_schemas import (
    CanonicalBuildingModel,
    SiteGeometry,
    BuildingLevel,
    WallSegment,
    RoomPolygon,
    Opening,
    StairFlight,
    RoofStructure,
)
from app.services.cbm_3d_generator import CBM3DGenerator

def test_cbm_3d_generator_pipeline():
    site = SiteGeometry(plot_width=25.0, plot_length=45.0, unit="feet", marla_size=5.0, total_area_sqft=1125.0)
    level0 = BuildingLevel(level_id="lvl_0", index=0, name="Ground Floor", elevation=0.0, height=11.0)
    level1 = BuildingLevel(level_id="lvl_1", index=1, name="First Floor", elevation=11.0, height=11.0)

    wall1 = WallSegment(id="w1", level_id="lvl_0", start=(0, 0), end=(25, 0), wall_type="exterior")
    wall2 = WallSegment(id="w1_dup", level_id="lvl_0", start=(0, 0), end=(25, 0), wall_type="interior") # duplicate to test deduplication

    room1 = RoomPolygon(id="r1", level_id="lvl_0", name="Living Room", room_type="living_room", polygon=[(0,0), (20,0), (20,15), (0,15)], area_sqft=300.0)
    opening1 = Opening(id="op1", wall_id="w1", level_id="lvl_0", opening_type="door", offset_from_start=5.0, width=3.5)
    stair1 = StairFlight(id="st1", level_id="lvl_0", target_level_id="lvl_1", start_point=(15, 10), end_point=(20, 10))
    roof1 = RoofStructure(id="roof_1", roof_type="gable", overhang=1.5)

    cbm = CanonicalBuildingModel(
        schema_version="1.0.0",
        project_id="test_3d_proj",
        title="5 Marla House 3D",
        site=site,
        levels=[level0, level1],
        walls=[wall1, wall2],
        rooms=[room1],
        openings=[opening1],
        stairs=[stair1],
        roof=roof1,
    )

    scene_payload = CBM3DGenerator.generate_3d_scene_payload(cbm)

    assert scene_payload["project_id"] == "test_3d_proj"
    assert len(scene_payload["levels"]) == 2
    assert len(scene_payload["rooms"]) == 1
    # Wall deduplication should result in 1 unique wall for (0,0)-(25,0) prioritizing exterior
    assert len(scene_payload["walls"]) == 1
    assert scene_payload["walls"][0]["wall_type"] == "exterior"
    assert len(scene_payload["openings"]) == 1
    assert len(scene_payload["stairs"]) == 1
    assert scene_payload["roof"]["roof_type"] == "gable"
