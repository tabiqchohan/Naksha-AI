from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

class FurnitureItem(BaseModel):
    id: str
    type: Literal["bed", "double_bed", "sofa", "l_sofa", "dining_table", "kitchen_counter", "commode", "bathtub", "sink", "car", "tv_unit"]
    x: float = Field(..., description="X coordinate relative to room origin")
    y: float = Field(..., description="Y coordinate relative to room origin")
    width: float
    length: float
    rotation: float = 0.0

class Door(BaseModel):
    id: str
    room_name: str
    wall: Literal["north", "south", "east", "west"]
    position: float = Field(..., description="Distance from wall start (ft)")
    width: float = 3.5
    swing: Literal["inward_left", "inward_right", "outward"] = "inward_left"

class Window(BaseModel):
    id: str
    room_name: str
    wall: Literal["north", "south", "east", "west"]
    position: float = Field(..., description="Distance from wall start (ft)")
    width: float = 4.0

class Room(BaseModel):
    id: str
    name: str
    type: Literal[
        "master_bedroom", "bedroom", "attached_bath", "powder_room",
        "kitchen", "dirty_kitchen", "living_room", "drawing_room",
        "dining_room", "garage", "lawn", "ots_duct", "balcony", "staircase",
        "shop", "office", "corridor", "parking", "ramp", "lift_shaft", "store"
    ]
    x: float = Field(..., description="Left top X coordinate on plot in feet")
    y: float = Field(..., description="Left top Y coordinate on plot in feet")
    width: float = Field(..., description="Width in feet (horizontal)")
    length: float = Field(..., description="Length in feet (vertical)")
    sqft: Optional[float] = None
    color: Optional[str] = None
    furniture: List[FurnitureItem] = []
    floor_level: Optional[int] = 0  # 0 = Ground, 1 = First etc

class Plot(BaseModel):
    width: float = Field(..., description="Plot width in feet")
    length: float = Field(..., description="Plot length in feet")
    unit: str = "feet"
    marla_size: Optional[float] = None
    total_area_sqft: Optional[float] = None

class MaterialEstimate(BaseModel):
    total_plot_sqft: float
    covered_area_sqft: float
    open_area_sqft: float
    bricks_count: int
    cement_bags: int
    steel_tons: float
    sand_cft: float
    crush_cft: float
    estimated_cost_pkr: float
    estimated_cost_usd: float
    breakdown: Dict[str, Any]

class FloorPlan(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    plot: Plot
    rooms: List[Room]
    doors: List[Door] = []
    windows: List[Window] = []
    material_estimate: Optional[MaterialEstimate] = None
    warnings: List[str] = []

class GeneratePlanRequest(BaseModel):
    prompt: Optional[str] = "Modern 3 Bed, 2 Bath open layout for 50x40 plot"
    plot_width: Optional[float] = 50.0
    plot_length: Optional[float] = 60.0
    plot_preset: Optional[str] = "custom" # "3_marla", "5_marla", "7_marla", "10_marla", "1_kanal", "custom"
    building_type: Optional[Literal["house", "plaza", "shop", "warehouse", "duplex"]] = "house" # Building type
    bedrooms: Optional[int] = 3
    bathrooms: Optional[int] = 2
    kitchen_type: Optional[str] = "open" # "open", "closed", "dirty_kitchen"
    floors: Optional[int] = 1
    style: Optional[str] = "modern" # "modern", "classical", "minimalist"
    road_facing: Optional[Literal["north", "south", "east", "west"]] = "east" # For setback calculation
    llm_provider: Optional[str] = "auto" # "auto", "gemini", "groq", "smart_rule"

class CostCalculationRequest(BaseModel):
    rooms: List[Room]
    plot_width: float
    plot_length: float
    rate_per_sqft_pkr: Optional[float] = 3200.0 # PKR per sqft grey structure
