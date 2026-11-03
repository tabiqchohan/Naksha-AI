from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.models.schemas import (
    FloorPlan, GeneratePlanRequest, CostCalculationRequest, MaterialEstimate, Plot
)
from app.services.ai_engine import AIEngine
from app.services.material_estimator import MaterialEstimator
from app.services.geometry_validator import GeometryValidator
from app.services.export_service import ExportService
from app.auth.dependencies import get_current_active_user, check_credits, deduct_credit
from app.database import get_db
from app.models.user_models import User

router = APIRouter(prefix="/plans", tags=["Floor Plans"])


class LayoutSuggestionRequest(BaseModel):
    plot_width: float
    plot_length: float
    building_type: Optional[str] = "house"
    floors: Optional[int] = 1
    style: Optional[str] = "modern"


class LayoutSuggestionResponse(BaseModel):
    suggestions: List[dict]
    recommended: dict
    analysis: str


@router.post("/generate", response_model=FloorPlan)
async def generate_plan(request: GeneratePlanRequest):
    """
    Generates a full 2D architectural floor plan from natural language prompt
    and plot constraints using AI / Intelligent geometric engine.
    """
    try:
        plan = await AIEngine.generate_floor_plan(request)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggest", response_model=LayoutSuggestionResponse)
async def suggest_layout(req: LayoutSuggestionRequest):
    """AI Layout Advisor - Suggest optimal room layout based on plot size"""
    try:
        area_sqft = req.plot_width * req.plot_length
        area_marla = area_sqft / 272.25
        suggestions = []
        
        if req.building_type == "house":
            if area_marla <= 3:
                suggestions = [
                    {"id": "opt1", "title": "2 Bed Compact Home", "rooms": ["2 Bedrooms", "1 Bath", "Living", "Kitchen", "Dining"], "coverage": "75%", "bedrooms": 2, "baths": 1, "parking": False, "description": "Efficient layout for small family"},
                    {"id": "opt2", "title": "3 Bed Smart Layout", "rooms": ["3 Bedrooms", "2 Baths", "Drawing", "Dining", "Kitchen"], "coverage": "80%", "bedrooms": 3, "baths": 2, "parking": False, "description": "Maximize space with open plan"},
                ]
            elif area_marla <= 5:
                suggestions = [
                    {"id": "opt1", "title": "3 Bed Modern Home", "rooms": ["3 Bedrooms (1 Master)", "3 Baths", "Drawing", "Dining", "Kitchen", "Store"], "coverage": "82%", "bedrooms": 3, "baths": 3, "parking": True, "description": "Perfect for nuclear family with parking"},
                    {"id": "opt2", "title": "4 Bed Family Home", "rooms": ["4 Bedrooms (2 Master)", "4 Baths", "Drawing", "Living", "Dining", "Kitchen", "Store", "Laundry"], "coverage": "85%", "bedrooms": 4, "baths": 4, "parking": True, "description": "Spacious layout for joint family"},
                    {"id": "opt3", "title": "3 Bed + Guest Room", "rooms": ["3 Bedrooms", "1 Guest Room", "3 Baths", "Drawing", "Dining", "Kitchen", "Store"], "coverage": "84%", "bedrooms": 4, "baths": 3, "parking": True, "description": "Great for entertaining guests"},
                ]
            elif area_marla <= 10:
                suggestions = [
                    {"id": "opt1", "title": "4 Bed Luxury Villa", "rooms": ["4 Bedrooms (2 Master)", "5 Baths", "Drawing", "Formal Dining", "Family Lounge", "Kitchen", "Store", "Laundry", "Garage"], "coverage": "80%", "bedrooms": 4, "baths": 5, "parking": True, "description": "Luxurious with ample space"},
                    {"id": "opt2", "title": "5 Bed Mansion Style", "rooms": ["5 Bedrooms (3 Master)", "6 Baths", "Drawing", "Dining", "TV Lounge", "Kitchen", "Pantry", "Store", "Servant Room", "Garage"], "coverage": "82%", "bedrooms": 5, "baths": 6, "parking": True, "description": "Grand design for large family"},
                ]
            else:
                suggestions = [
                    {"id": "opt1", "title": "6 Bed Estate Home", "rooms": ["6 Bedrooms", "7 Baths", "Multiple Lounges", "Formal/Informal Dining", "Kitchen", "Pantry", "Servant Quarters", "Garage", "Study"], "coverage": "78%", "bedrooms": 6, "baths": 7, "parking": True, "description": "Palatial design with all amenities"},
                ]
        elif req.building_type == "plaza":
            suggestions = [
                {"id": "opt1", "title": "Ground + First Floor Plaza", "rooms": ["Ground: 6-8 Shops", "First Floor: Offices/Flats", "Staircase", "Corridor", "Washrooms"], "coverage": "90%", "shops": 6, "offices": 4, "parking": True, "description": "Ideal for commercial rental income"},
                {"id": "opt2", "title": "Full Commercial Plaza", "rooms": ["Ground Floor Shops", "Mezzanine/Upper Floors", "Parking", "Elevator Shaft", "Common Areas"], "coverage": "92%", "shops": 10, "offices": 8, "parking": True, "description": "Maximize commercial space"},
            ]
        elif req.building_type == "shop":
            suggestions = [
                {"id": "opt1", "title": "Single Shop Unit", "rooms": ["Shop Floor", "Storage", "Toilet"], "coverage": "85%", "bedrooms": 0, "baths": 1, "parking": False, "description": "Simple retail space"},
            ]
        else:
            suggestions = [
                {"id": "opt1", "title": "Standard Layout", "rooms": ["Living", "Kitchen", "Bedrooms", "Baths"], "coverage": "80%", "bedrooms": 3, "baths": 2, "parking": True, "description": "Flexible layout"},
            ]
        
        recommended = suggestions[0] if suggestions else {}
        analysis = f"For {req.plot_width}x{req.plot_length} ft ({area_marla:.1f} Marla), {req.building_type} with {req.floors} floor(s). Best utilization suggests {recommended.get('title', 'custom layout')} with {recommended.get('coverage', '80%')} coverage."
        
        return LayoutSuggestionResponse(suggestions=suggestions, recommended=recommended, analysis=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calculate-cost", response_model=MaterialEstimate)
async def calculate_material_cost(req: CostCalculationRequest):
    """Calculates building materials (bricks, cement, steel) & budget in PKR/USD."""
    plot = Plot(width=req.plot_width, length=req.plot_length, unit="feet")
    return MaterialEstimator.calculate_estimate(plot, req.rooms, rate_per_sqft=req.rate_per_sqft_pkr)

@router.post("/validate-layout")
async def validate_layout(plan: FloorPlan):
    """Validates room boundaries, overlaps, and returns adjusted layout with warnings."""
    rooms, warnings = GeometryValidator.validate_and_correct_layout(plan.plot, plan.rooms)
    plan.rooms = rooms
    plan.warnings = warnings
    plan.material_estimate = MaterialEstimator.calculate_estimate(plan.plot, rooms)
    return plan

@router.post("/export-pdf")
async def export_blueprint_pdf(plan: FloorPlan):
    """Exports blueprint PDF with dimensions and bill of materials."""
    try:
        pdf_bytes = ExportService.generate_blueprint_pdf(plan, add_watermark=False)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=nakshai_{plan.id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/export-dxf")
async def export_blueprint_dxf(plan: FloorPlan):
    """Exports CAD DXF file for AutoCAD, LibreCAD and other CAD software."""
    try:
        dxf_bytes = ExportService.generate_dxf(plan, add_watermark=False)
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename=nakshai_{plan.id}.dxf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DXF generation failed: {str(e)}")

@router.get("/presets")
async def get_plot_presets():
    """Get available plot presets for Pakistani/South Asian standards"""
    from app.services.ai_engine import PLOT_PRESETS
    return {
        "presets": PLOT_PRESETS,
        "building_types": ["house", "plaza", "shop", "warehouse", "duplex"],
        "styles": ["modern", "classical", "minimalist"]
    }
