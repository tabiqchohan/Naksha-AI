from typing import Dict, Any, List
from app.models.schemas import FloorPlan, VastuReport, VastuAdvice

class DesignAdvisor:
    @staticmethod
    def impact_summary(plan: FloorPlan) -> Dict[str, Any]:
        total = max(1.0, plan.plot.width * plan.plot.length)
        covered = sum((r.width * r.length) for r in plan.rooms if getattr(r, "type", "") not in ["lawn", "ots_duct", "balcony", "parking"])
        open_area = max(0.0, total - covered)
        est = plan.material_estimate.model_dump() if plan.material_estimate else {}
        # Sun/ventilation concept heuristics
        sun = {"morning_east": "Place bedrooms/kitchen openings to catch morning light where practical.", "afternoon_west": "Use shading/vertical fins/trees on west if possible.", "cross_ventilation": "Try openings on opposite sides for living/bedrooms; avoid deep unventilated cores."}
        has_openings = len(getattr(plan, "windows", []) or []) + len(getattr(plan, "doors", []) or [])
        if has_openings < max(3, len(plan.rooms)//2): sun["warning"] = "Low opening count detected (concept) — verify window/vent sizes with architect/bylaws."
        # Structural/MEP concept hooks (no engineering)
        structural = {"system": "RCC frame/load-bearing concept only", "notes": ["Column/beam/slab sizes require structural engineer design.", "Avoid removing/modifying walls without engineer approval."]}
        mep = {"electrical": "Provide DB, lighting/power circuits, AC points conceptually; detailed load calc by engineer.", "plumbing": "Group wet areas where practical; slopes/venting/septic/sewer by licensed plumber/engineer.", "hvac": "Cross-ventilation first; AC tonnage/ducting requires site-specific design."}
        return {
            "total_area_sqft": round(total, 1),
            "covered_area_sqft": round(covered, 1),
            "open_area_sqft": round(open_area, 1),
            "coverage_percent": round((covered / total) * 100, 1),
            "rooms_count": len(plan.rooms),
            "estimated_cost_pkr": est.get("estimated_cost_pkr"),
            "estimated_cost_usd": est.get("estimated_cost_usd"),
            "bylaws_status": (plan.bylaws_report or {}).get("passed") if isinstance(plan.bylaws_report, dict) else None,
            "sun_ventilation": sun,
            "structural_concept": structural,
            "mep_concept": mep,
            "notes": ["Moving rooms/walls changes coverage, cost, bylaw checks, and concept sun/ventilation behavior. Use Recalculate to refresh."],
        }

    @staticmethod
    def compare_variants(variants: List[Dict[str, Any]]) -> Dict[str, Any]:
        rows = []
        for v in variants:
            est = v.get("material_estimate") or {}
            rows.append({"id": v.get("id"), "title": v.get("title"), "cost_pkr": est.get("estimated_cost_pkr"), "covered_area_sqft": est.get("covered_area_sqft"), "rooms": len(v.get("rooms") or []), "bylaws_passed": (v.get("bylaws_report") or {}).get("passed")})
        best_cost = min((r for r in rows if r.get("cost_pkr")), key=lambda r: r["cost_pkr"], default=None)
        return {"rows": rows, "recommendation": (f"Lowest estimated cost: {best_cost['title']}" if best_cost else "Compare coverage, cost, and bylaw status before selecting.")}

    @staticmethod
    def vastu_report(plan: FloorPlan) -> VastuReport:
        items: List[VastuAdvice] = []
        score = 80
        w, l = plan.plot.width, plan.plot.length
        for r in plan.rooms:
            cx, cy = r.x + r.width / 2, r.y + r.length / 2
            nx, ny = cx / max(w, 1), cy / max(l, 1)
            zone = "NE" if nx > 0.5 and ny < 0.33 else "SE" if nx > 0.5 and ny > 0.66 else "SW" if nx < 0.33 and ny > 0.66 else "NW" if nx < 0.33 and ny < 0.33 else "center"
            t = (r.type or "").lower()
            status, advice = "good", "Placement appears acceptable (advisory)."
            if t == "kitchen" and zone in ["NE", "NW"]:
                status, advice, score = "caution", "Kitchen is often preferred in SE; verify practicality, ventilation, and bylaws.", score - 4
            elif t == "kitchen" and zone == "SE":
                advice = "Kitchen in SE aligns with common Vastu preference (advisory)."
            elif t == "master_bedroom" and zone == "NE":
                status, advice, score = "caution", "Master bedroom is commonly preferred in SW; NE is often kept lighter/open.", score - 3
            elif t in ["attached_bath", "powder_room"] and zone == "NE":
                status, advice, score = "avoid", "Toilets in NE are commonly discouraged in Vastu; consider relocation if feasible.", score - 6
            elif t in ["living_room", "drawing_room"] and zone in ["NE", "NW"]:
                advice = "Living/drawing in north zones is commonly considered favorable (advisory)."
            items.append(VastuAdvice(room=r.name, status=status, advice=f"{zone.upper()} zone: {advice}"))
        summary = "Good advisory alignment." if score >= 75 else "Some Vastu cautions found; review suggestions before finalizing."
        return VastuReport(score=max(0, min(100, score)), summary=summary, items=items)
