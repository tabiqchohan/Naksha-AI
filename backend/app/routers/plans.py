from fastapi import APIRouter, HTTPException, Response, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.models.schemas import FloorPlan, GeneratePlanRequest, CostCalculationRequest, MaterialEstimate, Plot
from app.services.ai_engine import AIEngine
from app.services.material_estimator import MaterialEstimator
from app.services.geometry_validator import GeometryValidator
from app.services.export_service import ExportService
from app.services.bylaws_engine import BylawsEngine
from app.services.design_advisor import DesignAdvisor
from app.models.cbm_schemas import CanonicalBuildingModel
from app.services.cbm_adapter import CBMAdapter
from app.services.architectural_drawing_service import ArchitecturalDrawingService
from app.services.boq_service import BOQService
from app.auth.dependencies import check_credits, deduct_credit, get_optional_user, get_current_active_user
from app.database import get_db
from app.models.project_models import Project
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


class RecalculateRequest(BaseModel):
    plan: FloorPlan
    rate_per_sqft_pkr: Optional[float] = None
    bylaws_pack: Optional[str] = None


class VariantsRequest(BaseModel):
    base: GeneratePlanRequest
    count: Optional[int] = 3


def _enrich_plan(plan: FloorPlan, bylaws_pack: Optional[str] = None) -> FloorPlan:
    if not plan.material_estimate:
        plan.material_estimate = MaterialEstimator.calculate_estimate(plan.plot, plan.rooms)
    plan.bylaws_report = BylawsEngine.evaluate(plan, bylaws_pack).model_dump()
    plan.vastu_report = DesignAdvisor.vastu_report(plan).model_dump()
    plan.impact_summary = DesignAdvisor.impact_summary(plan)
    plan.disclaimer = "AI-generated concept. Verify dimensions/bylaws with licensed architect/engineer and local authority before construction."
    return plan


@router.post("/generate", response_model=FloorPlan)
async def generate_plan(request: GeneratePlanRequest, db: Session = Depends(get_db), current_user: User = Depends(check_credits)):
    try:
        plan = await AIEngine.generate_floor_plan(request)
        _enrich_plan(plan, getattr(request, "bylaws_pack", None))
        deduct_credit(current_user, db)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-variants")
async def generate_variants(req: VariantsRequest, db: Session = Depends(get_db), current_user: User = Depends(check_credits)):
    count = max(1, min(req.count or 3, 3))
    styles = ["modern", "minimalist", "classical"]
    variants = []
    for i in range(count):
        base = req.base
        variant_req = base.model_copy(update={"style": styles[i % len(styles)], "bedrooms": max(1, (base.bedrooms or 3) + (i - 1 if i else 0))})
        plan = await AIEngine.generate_floor_plan(variant_req)
        plan.title = f"{plan.title} - Option {chr(65+i)}"
        _enrich_plan(plan, getattr(base, "bylaws_pack", None))
        variants.append(plan.model_dump())
    deduct_credit(current_user, db)
    return {"variants": variants, "compare": DesignAdvisor.compare_variants(variants)}


@router.post("/suggest", response_model=LayoutSuggestionResponse)
async def suggest_layout(req: LayoutSuggestionRequest):
    try:
        area_sqft = req.plot_width * req.plot_length
        area_marla = area_sqft / 272.25
        suggestions = []
        if req.building_type == "house":
            if area_marla <= 3:
                suggestions = [{"id":"opt1","title":"2 Bed Compact Home","rooms":["2 Bedrooms","1 Bath","Living","Kitchen"],"coverage":"75%","bedrooms":2,"baths":1,"parking":False,"description":"Efficient layout for small family"},{"id":"opt2","title":"3 Bed Smart Layout","rooms":["3 Bedrooms","2 Baths","Drawing","Kitchen"],"coverage":"80%","bedrooms":3,"baths":2,"parking":False,"description":"Maximize space with open plan"}]
            elif area_marla <= 5:
                suggestions = [{"id":"opt1","title":"3 Bed Modern Home","rooms":["3 Bedrooms","3 Baths","Drawing","Dining","Kitchen","Store"],"coverage":"82%","bedrooms":3,"baths":3,"parking":True,"description":"Perfect for nuclear family with parking"},{"id":"opt2","title":"4 Bed Family Home","rooms":["4 Bedrooms","4 Baths","Drawing","Living","Kitchen","Store"],"coverage":"85%","bedrooms":4,"baths":4,"parking":True,"description":"Spacious layout for joint family"}]
            elif area_marla <= 10:
                suggestions = [{"id":"opt1","title":"4 Bed Luxury Villa","rooms":["4 Bedrooms","5 Baths","Drawing","Dining","Lounge","Kitchen","Garage"],"coverage":"80%","bedrooms":4,"baths":5,"parking":True,"description":"Luxurious with ample space"},{"id":"opt2","title":"5 Bed Mansion Style","rooms":["5 Bedrooms","6 Baths","Drawing","Dining","TV Lounge","Kitchen","Servant Room"],"coverage":"82%","bedrooms":5,"baths":6,"parking":True,"description":"Grand design for large family"}]
            else:
                suggestions = [{"id":"opt1","title":"6 Bed Estate Home","rooms":["6 Bedrooms","7 Baths","Multiple Lounges","Kitchen","Servant Quarters","Garage"],"coverage":"78%","bedrooms":6,"baths":7,"parking":True,"description":"Palatial design with all amenities"}]
        elif req.building_type == "plaza":
            suggestions = [{"id":"opt1","title":"Ground + First Floor Plaza","rooms":["Ground Shops","First Floor Offices","Staircase","Washrooms"],"coverage":"90%","shops":6,"offices":4,"parking":True,"description":"Ideal for commercial rental income"}]
        elif req.building_type == "shop":
            suggestions = [{"id":"opt1","title":"Single Shop Unit","rooms":["Shop Floor","Storage","Toilet"],"coverage":"85%","bedrooms":0,"baths":1,"parking":False,"description":"Simple retail space"}]
        else:
            suggestions = [{"id":"opt1","title":"Standard Layout","rooms":["Living","Kitchen","Bedrooms","Baths"],"coverage":"80%","bedrooms":3,"baths":2,"parking":True,"description":"Flexible layout"}]
        recommended = suggestions[0] if suggestions else {}
        analysis = f"For {req.plot_width}x{req.plot_length} ft ({area_marla:.1f} Marla), {req.building_type} with {req.floors} floor(s): {recommended.get('title','custom layout')}."
        return LayoutSuggestionResponse(suggestions=suggestions, recommended=recommended, analysis=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-cost", response_model=MaterialEstimate)
async def calculate_material_cost(req: CostCalculationRequest):
    plot = Plot(width=req.plot_width, length=req.plot_length, unit="feet")
    return MaterialEstimator.calculate_estimate(plot, req.rooms, rate_per_sqft=req.rate_per_sqft_pkr)


@router.post("/recalculate", response_model=FloorPlan)
async def recalculate_plan(req: RecalculateRequest):
    plan = req.plan
    rooms, warnings = GeometryValidator.validate_and_correct_layout(plan.plot, plan.rooms)
    plan.rooms = rooms
    plan.warnings = warnings
    plan.material_estimate = MaterialEstimator.calculate_estimate(plan.plot, rooms, rate_per_sqft=req.rate_per_sqft_pkr or 3200.0)
    return _enrich_plan(plan, req.bylaws_pack)


@router.post("/validate-layout")
async def validate_layout(plan: FloorPlan, bylaws_pack: Optional[str] = None):
    rooms, warnings = GeometryValidator.validate_and_correct_layout(plan.plot, plan.rooms)
    plan.rooms = rooms
    plan.warnings = warnings
    plan.material_estimate = MaterialEstimator.calculate_estimate(plan.plot, rooms)
    _enrich_plan(plan, bylaws_pack)
    return plan


@router.get("/bylaws-packs")
async def get_bylaws_packs():
    return {"packs": BylawsEngine.packs()}


@router.post("/export-pdf")
async def export_blueprint_pdf(plan: FloorPlan, bylaws_pack: Optional[str] = None, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    try:
        _enrich_plan(plan, bylaws_pack)
        is_paid = bool(current_user and (getattr(current_user, 'plan_type', None) and str(getattr(current_user.plan_type, 'value', current_user.plan_type)) in ['pro','enterprise']))
        pdf_bytes = ExportService.generate_blueprint_pdf(plan, add_watermark=not is_paid)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=nakshai_{plan.id}.pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/export-dxf")
async def export_blueprint_dxf(plan: FloorPlan, bylaws_pack: Optional[str] = None, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_optional_user)):
    try:
        _enrich_plan(plan, bylaws_pack)
        is_paid = bool(current_user and (getattr(current_user, 'plan_type', None) and str(getattr(current_user.plan_type, 'value', current_user.plan_type)) in ['pro','enterprise']))
        dxf_bytes = ExportService.generate_dxf(plan, add_watermark=not is_paid)
        return Response(content=dxf_bytes, media_type="application/dxf", headers={"Content-Disposition": f"attachment; filename=nakshai_{plan.id}.dxf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DXF generation failed: {str(e)}")


@router.post("/cbm-drawings")
async def get_cbm_drawings(plan: FloorPlan, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        # Optional DB ownership check if plan.id corresponds to a saved project
        project = db.query(Project).filter(Project.project_id == plan.id).first()
        if project and project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access forbidden: unauthorized project access")

        cbm = CBMAdapter.to_cbm(plan)
        errors = CBMAdapter.validate_cbm(cbm)
        if errors:
            return {"status": "warning", "warnings": errors, "drawings": ArchitecturalDrawingService.generate_drawings_payload(cbm)}
        return {"status": "success", "drawings": ArchitecturalDrawingService.generate_drawings_payload(cbm)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBM drawings generation failed: {str(e)}")


@router.post("/cbm-export-pdf")
async def export_cbm_pdf(plan: FloorPlan, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        project = db.query(Project).filter(Project.project_id == plan.id).first()
        if project and project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access forbidden: unauthorized project access")

        cbm = CBMAdapter.to_cbm(plan)
        errors = CBMAdapter.validate_cbm(cbm)
        if errors and any("non-existent" in err for err in errors):
            raise HTTPException(status_code=400, detail=f"Invalid CBM payload: {errors}")

        is_paid = bool(getattr(current_user, 'plan_type', None) and str(getattr(current_user.plan_type, 'value', current_user.plan_type)) in ['pro','enterprise'])
        pdf_bytes = ArchitecturalDrawingService.generate_architectural_pdf(cbm, add_watermark=not is_paid)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=nakshai_architectural_{plan.id}.pdf"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBM PDF export failed: {str(e)}")


@router.post("/cbm-export-dxf")
async def export_cbm_dxf(plan: FloorPlan, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        project = db.query(Project).filter(Project.project_id == plan.id).first()
        if project and project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access forbidden: unauthorized project access")

        cbm = CBMAdapter.to_cbm(plan)
        errors = CBMAdapter.validate_cbm(cbm)
        if errors and any("non-existent" in err for err in errors):
            raise HTTPException(status_code=400, detail=f"Invalid CBM payload: {errors}")

        is_paid = bool(getattr(current_user, 'plan_type', None) and str(getattr(current_user.plan_type, 'value', current_user.plan_type)) in ['pro','enterprise'])
        dxf_bytes = ArchitecturalDrawingService.generate_dxf(cbm, add_watermark=not is_paid)
        return Response(content=dxf_bytes, media_type="application/dxf", headers={"Content-Disposition": f"attachment; filename=nakshai_architectural_{plan.id}.dxf"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBM DXF export failed: {str(e)}")


@router.post("/cbm-update")
async def update_cbm(cbm: CanonicalBuildingModel, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        # Optional project check
        project = db.query(Project).filter(Project.project_id == cbm.project_id).first()
        if project and project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access forbidden: unauthorized project access")

        errors = CBMAdapter.validate_cbm(cbm)
        floor_plan = CBMAdapter.from_cbm(cbm)
        estimate = MaterialEstimator.calculate_estimate(floor_plan.plot, floor_plan.rooms)

        return {
            "status": "warning" if errors else "success",
            "warnings": errors,
            "cbm": cbm.dict(),
            "floor_plan": floor_plan.dict(),
            "material_estimate": estimate.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBM update synchronization failed: {str(e)}")


@router.post("/cbm-boq")
async def generate_cbm_boq(cbm: CanonicalBuildingModel, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        project = db.query(Project).filter(Project.project_id == cbm.project_id).first()
        if project and project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access forbidden: unauthorized project access")

        boq = BOQService.generate_boq(cbm)
        return {"status": "success", "boq": boq}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBM BOQ generation failed: {str(e)}")


@router.post("/cbm-compliance")
async def evaluate_cbm_compliance(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    try:
        cbm_data = payload.get("cbm")
        pack_id = payload.get("pack_id", "pakistan_generic")
        if not cbm_data:
            raise HTTPException(status_code=400, detail="Missing cbm payload")

        cbm = CanonicalBuildingModel(**cbm_data)
        project = db.query(Project).filter(Project.project_id == cbm.project_id).first()
        if project and project.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access forbidden: unauthorized project access")

        report = BylawsEngine.evaluate_cbm(cbm, pack_id)
        return {"status": "success", "compliance_report": report}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CBM compliance evaluation failed: {str(e)}")


@router.get("/bylaws/packs")
async def get_bylaws_packs():
    return {"status": "success", "packs": BylawsEngine.packs()}





@router.get("/presets")
async def get_plot_presets():
    from app.services.ai_engine import PLOT_PRESETS
    return {"presets": PLOT_PRESETS, "building_types": ["house", "plaza", "shop", "warehouse", "duplex"], "styles": ["modern", "classical", "minimalist"]}
