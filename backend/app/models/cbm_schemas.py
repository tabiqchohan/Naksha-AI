from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any, Tuple

class SiteGeometry(BaseModel):
    plot_width: float = Field(..., description="Plot width in feet")
    plot_length: float = Field(..., description="Plot length in feet")
    unit: str = "feet"
    marla_size: Optional[float] = None
    total_area_sqft: Optional[float] = None
    setbacks: Dict[str, float] = Field(
        default_factory=lambda: {"front": 6.0, "rear": 6.0, "left": 3.0, "right": 3.0},
        description="Setbacks in feet"
    )

class BuildingLevel(BaseModel):
    level_id: str = Field(..., description="Unique level identifier e.g. 'lvl_0'")
    index: int = Field(..., description="0 for ground, 1 for first floor, etc.")
    name: str = Field(..., description="Level display name e.g. 'Ground Floor'")
    elevation: float = Field(0.0, description="Elevation from ground in feet")
    height: float = Field(11.0, description="Floor-to-floor or floor-to-ceiling height in feet")
    slab_thickness: float = Field(0.75, description="Slab thickness in feet")

class WallSegment(BaseModel):
    id: str = Field(..., description="Unique wall ID")
    level_id: str = Field(..., description="Associated level ID")
    start: Tuple[float, float] = Field(..., description="(x, y) start coordinates in feet")
    end: Tuple[float, float] = Field(..., description="(x, y) end coordinates in feet")
    thickness: float = Field(0.75, description="Wall thickness in feet (e.g. 0.75 for 9-in brick)")
    wall_type: Literal["exterior", "interior", "partition", "boundary"] = Field("exterior")
    material: str = Field("brick_masonry")

class RoomPolygon(BaseModel):
    id: str = Field(..., description="Unique room ID")
    level_id: str = Field(..., description="Associated level ID")
    name: str = Field(..., description="Room name")
    room_type: str = Field(..., description="Normalized room type")
    polygon: List[Tuple[float, float]] = Field(..., description="List of (x, y) vertex coordinates forming room boundary")
    area_sqft: float = Field(..., description="Calculated area in sq ft")
    color: Optional[str] = None
    ceiling_height: Optional[float] = None

class Opening(BaseModel):
    id: str = Field(..., description="Unique opening ID")
    wall_id: str = Field(..., description="Reference wall ID where opening is placed")
    level_id: str = Field(..., description="Associated level ID")
    opening_type: Literal["door", "window", "ventilator", "arch"] = Field("door")
    offset_from_start: float = Field(..., description="Distance from wall start point in feet")
    width: float = Field(3.5, description="Opening width in feet")
    height: float = Field(7.0, description="Opening height in feet")
    sill_height: float = Field(0.0, description="Sill height from floor in feet")
    swing: Optional[Literal["inward_left", "inward_right", "outward", "sliding"]] = "inward_left"

class FloorSlab(BaseModel):
    id: str = Field(..., description="Unique slab ID")
    level_id: str = Field(..., description="Associated level ID")
    polygon: List[Tuple[float, float]] = Field(..., description="Slab perimeter polygon vertices")
    thickness: float = Field(0.75, description="Slab thickness in feet")

class StairFlight(BaseModel):
    id: str = Field(..., description="Unique staircase ID")
    level_id: str = Field(..., description="Starting level ID")
    target_level_id: str = Field(..., description="Destination level ID")
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    width: float = Field(3.5, description="Stair width in feet")
    riser_count: int = Field(18, description="Total risers")

class RoofStructure(BaseModel):
    id: str = Field(..., description="Unique roof ID")
    roof_type: Literal["flat_parapet", "gable", "hip", "dome"] = Field("flat_parapet")
    overhang: float = Field(1.0, description="Roof overhang in feet")
    pitch_angle: float = Field(0.0, description="Roof pitch angle in degrees")

class CanonicalBuildingModel(BaseModel):
    schema_version: str = Field("1.0.0", description="CBM schema version")
    project_id: str = Field(..., description="Project identifier")
    title: str = Field(..., description="Project title")
    description: Optional[str] = None
    site: SiteGeometry
    levels: List[BuildingLevel] = Field(default_factory=list)
    walls: List[WallSegment] = Field(default_factory=list)
    rooms: List[RoomPolygon] = Field(default_factory=list)
    openings: List[Opening] = Field(default_factory=list)
    slabs: List[FloorSlab] = Field(default_factory=list)
    stairs: List[StairFlight] = Field(default_factory=list)
    roof: Optional[RoofStructure] = None
    material_estimate: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
