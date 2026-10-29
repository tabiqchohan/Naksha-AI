from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from typing import List
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

@router.post("/generate", response_model=FloorPlan)
async def generate_plan(request: GeneratePlanRequest, current_user: User = Depends(check_credits), db: Session = Depends(get_db)):
    """
    Generates a full 2D architectural floor plan from natural language prompt
    and plot constraints using AI / Intelligent geometric engine.
    """
    try:
        plan = await AIEngine.generate_floor_plan(request)
        deduct_credit(current_user, db)
        return plan
    except HTTPException:
        raise
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
async def export_blueprint_pdf(plan: FloorPlan, current_user: User = Depends(get_current_active_user)):
    """Exports blueprint PDF with dimensions and bill of materials."""
    try:
        add_watermark = current_user.plan_type.value == "free"
        pdf_bytes = ExportService.generate_blueprint_pdf(plan, add_watermark=add_watermark)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=nakshai_{plan.id}.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.post("/export-dxf")
async def export_blueprint_dxf(plan: FloorPlan, current_user: User = Depends(get_current_active_user)):
    """Exports CAD DXF file for AutoCAD, LibreCAD and other CAD software."""
    try:
        add_watermark = current_user.plan_type.value == "free"
        dxf_bytes = ExportService.generate_dxf(plan, add_watermark=add_watermark)
        return Response(
            content=dxf_bytes,
            media_type="application/dxf",
            headers={"Content-Disposition": f"attachment; filename=nakshai_{plan.id}.dxf"}
        )
    except HTTPException:
        raise
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
