from typing import Dict, Any, List
from app.models.schemas import FloorPlan, BylawsReport, BylawsCheck
from app.models.cbm_schemas import CanonicalBuildingModel

PACKS = {
    "pakistan_generic": {
        "name": "Pakistan Generic Residential (Concept)",
        "front": 5.0,
        "rear": 5.0,
        "side": 3.0,
        "coverage": 75.0,
        "max_far": 2.0,
        "max_height_ft": 35.0,
        "max_storeys": 2,
        "parking": False,
        "notes": "Typical small-plot concept checks; verify local authority/DHA/LDA/CDA rules."
    },
    "dha_lahore": {
        "name": "DHA Lahore (Concept)",
        "front": 5.0,
        "rear": 5.0,
        "side": 5.0,
        "coverage": 70.0,
        "max_far": 1.8,
        "max_height_ft": 38.0,
        "max_storeys": 2,
        "parking": True,
        "notes": "Concept-level. Actual DHA by-laws vary by phase/plot/category; verify current DHA Lahore regulations."
    },
    "lda_lahore": {
        "name": "LDA / Punjab (Concept)",
        "front": 5.0,
        "rear": 5.0,
        "side": 5.0,
        "coverage": 72.0,
        "max_far": 2.0,
        "max_height_ft": 35.0,
        "max_storeys": 2,
        "parking": True,
        "notes": "Concept-level. Verify latest LDA/Punjab building regulations and approved plan conditions."
    },
    "cda_islamabad": {
        "name": "CDA Islamabad (Concept)",
        "front": 10.0,
        "rear": 10.0,
        "side": 5.0,
        "coverage": 65.0,
        "max_far": 1.5,
        "max_height_ft": 32.0,
        "max_storeys": 2,
        "parking": True,
        "notes": "Concept-level. CDA rules vary by zone/plot size; verify current CDA by-laws."
    },
    "sbca_karachi": {
        "name": "SBCA Karachi (Concept)",
        "front": 5.0,
        "rear": 5.0,
        "side": 3.0,
        "coverage": 70.0,
        "max_far": 2.2,
        "max_height_ft": 40.0,
        "max_storeys": 3,
        "parking": True,
        "notes": "Concept-level. Verify SBCA Karachi Building & Town Planning Regulations for plot category."
    },
}

class BylawsEngine:
    @staticmethod
    def packs():
        return [{"id": k, **v} for k, v in PACKS.items()]

    @staticmethod
    def evaluate(plan: FloorPlan, pack_id: str = None) -> BylawsReport:
        pack_id = pack_id or "pakistan_generic"
        pack = PACKS.get(pack_id, PACKS["pakistan_generic"])
        checks: List[BylawsCheck] = []
        w, l = plan.plot.width, plan.plot.length
        covered = sum((r.width * r.length) for r in plan.rooms if getattr(r, "type", "") not in ["lawn", "ots_duct", "balcony", "parking"])
        coverage = (covered / max(1.0, w * l)) * 100
        minx = min((r.x for r in plan.rooms), default=0)
        miny = min((r.y for r in plan.rooms), default=0)
        maxx = max(((r.x + r.width) for r in plan.rooms), default=0)
        maxy = max(((r.y + r.length) for r in plan.rooms), default=0)
        front = miny
        rear = max(0, l - maxy)
        left = minx
        right = max(0, w - maxx)

        checks.append(BylawsCheck(id="coverage", title="Ground coverage", status="pass" if coverage <= pack["coverage"] + 0.1 else "fail", detail=f"Coverage {coverage:.1f}% (limit ~{pack['coverage']}%).", required=f"<= {pack['coverage']}%", actual=f"{coverage:.1f}%"))
        checks.append(BylawsCheck(id="front", title="Front setback (concept)", status="pass" if front >= pack["front"] - 0.1 else "warn", detail=f"Observed front clearance {front:.1f} ft.", required=f">= {pack['front']} ft", actual=f"{front:.1f} ft"))
        checks.append(BylawsCheck(id="rear", title="Rear setback (concept)", status="pass" if rear >= pack["rear"] - 0.1 else "warn", detail=f"Observed rear clearance {rear:.1f} ft.", required=f">= {pack['rear']} ft", actual=f"{rear:.1f} ft"))
        checks.append(BylawsCheck(id="left", title="Left setback (concept)", status="pass" if left >= pack["side"] - 0.1 else "warn", detail=f"Observed left clearance {left:.1f} ft.", required=f">= {pack['side']} ft", actual=f"{left:.1f} ft"))
        checks.append(BylawsCheck(id="right", title="Right setback (concept)", status="pass" if right >= pack["side"] - 0.1 else "warn", detail=f"Observed right clearance {right:.1f} ft.", required=f">= {pack['side']} ft", actual=f"{right:.1f} ft"))

        if pack.get("parking"):
            has_parking = any(getattr(r, "type", "") in ["garage", "parking"] or "parking" in (r.name or "").lower() for r in plan.rooms)
            checks.append(BylawsCheck(id="parking", title="Parking provision (concept)", status="pass" if has_parking else "warn", detail="Parking/garage found." if has_parking else "No explicit parking/garage detected; verify requirement.", required="As per authority/plot category", actual="Present" if has_parking else "Not detected"))

        passed = all(c.status == "pass" for c in checks)
        return BylawsReport(pack_id=pack_id, pack_name=pack["name"], passed=passed, checks=checks, notes=[pack["notes"], "Automated checks are approximate and based on room bounding extents, not a legal submission drawing."])

    @staticmethod
    def evaluate_cbm(cbm: CanonicalBuildingModel, pack_id: str = None) -> Dict[str, Any]:
        pack_id = pack_id or "pakistan_generic"
        pack = PACKS.get(pack_id, PACKS["pakistan_generic"])
        plot_w = cbm.site.plot_width
        plot_l = cbm.site.plot_length
        plot_area = plot_w * plot_l

        ground_rooms = [r for r in cbm.rooms if r.level_id == (cbm.levels[0].level_id if cbm.levels else "lvl_0") and r.room_type not in ["lawn", "ots_duct", "balcony"]]
        ground_covered = sum(r.area_sqft for r in ground_rooms)
        coverage_pct = round((ground_covered / max(1.0, plot_area)) * 100, 1)

        total_countable_area = sum(r.area_sqft for r in cbm.rooms if r.room_type not in ["lawn", "ots_duct"])
        far = round(total_countable_area / max(1.0, plot_area), 2)

        storeys = len(cbm.levels)
        max_height = max((lvl.elevation + lvl.height for lvl in cbm.levels), default=11.0)

        # Setback computation from room extents
        min_x = min((min(pt[0] for pt in r.polygon) for r in cbm.rooms), default=0)
        min_y = min((min(pt[1] for pt in r.polygon) for r in cbm.rooms), default=0)
        max_x = max((max(pt[0] for pt in r.polygon) for r in cbm.rooms), default=plot_w)
        max_y = max((max(pt[1] for pt in r.polygon) for r in cbm.rooms), default=plot_l)

        front = round(min_y, 1)
        rear = round(max(0, plot_l - max_y), 1)
        left = round(min_x, 1)
        right = round(max(0, plot_w - max_x), 1)

        checks = [
            {
                "id": "coverage",
                "title": "Ground Coverage",
                "status": "COMPLIANT" if coverage_pct <= pack["coverage"] + 0.1 else "NON_COMPLIANT",
                "required": f"<= {pack['coverage']}%",
                "actual": f"{coverage_pct}%",
                "detail": f"Ground footprint coverage is {coverage_pct}% against max allowed {pack['coverage']}%."
            },
            {
                "id": "far",
                "title": "Floor Area Ratio (FAR)",
                "status": "COMPLIANT" if far <= pack["max_far"] + 0.05 else "NON_COMPLIANT",
                "required": f"<= {pack['max_far']}",
                "actual": f"{far}",
                "detail": f"Calculated FAR is {far} against limit {pack['max_far']}."
            },
            {
                "id": "front_setback",
                "title": "Front Setback",
                "status": "COMPLIANT" if front >= pack["front"] - 0.1 else "WARNING",
                "required": f">= {pack['front']} ft",
                "actual": f"{front} ft",
                "detail": f"Front clearance is {front} ft."
            },
            {
                "id": "rear_setback",
                "title": "Rear Setback",
                "status": "COMPLIANT" if rear >= pack["rear"] - 0.1 else "WARNING",
                "required": f">= {pack['rear']} ft",
                "actual": f"{rear} ft",
                "detail": f"Rear clearance is {rear} ft."
            },
            {
                "id": "storeys",
                "title": "Storey Count",
                "status": "COMPLIANT" if storeys <= pack["max_storeys"] else "NON_COMPLIANT",
                "required": f"<= {pack['max_storeys']} storeys",
                "actual": f"{storeys} storeys",
                "detail": f"Building has {storeys} levels."
            }
        ]

        all_compliant = all(c["status"] == "COMPLIANT" for c in checks)
        overall_status = "COMPLIANT" if all_compliant else "WARNING"

        return {
            "project_id": cbm.project_id,
            "pack_id": pack_id,
            "pack_name": pack["name"],
            "overall_status": overall_status,
            "checks": checks,
            "notes": [pack["notes"], "Deterministic CBM-driven compliance evaluation."]
        }
