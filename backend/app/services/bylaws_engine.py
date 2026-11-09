from typing import Dict, Any, List
from app.models.schemas import FloorPlan, BylawsReport, BylawsCheck

PACKS = {
    "pakistan_generic": {"name": "Pakistan Generic Residential (Concept)", "front": 5, "rear": 5, "side": 3, "coverage": 75, "parking": False, "notes": "Typical small-plot concept checks; verify local authority/DHA/LDA/CDA rules."},
    "dha_lahore": {"name": "DHA Lahore (Concept)", "front": 5, "rear": 5, "side": 5, "coverage": 70, "parking": True, "notes": "Concept-level. Actual DHA by-laws vary by phase/plot/category; verify current DHA Lahore regulations."},
    "lda_lahore": {"name": "LDA / Punjab (Concept)", "front": 5, "rear": 5, "side": 5, "coverage": 72, "parking": True, "notes": "Concept-level. Verify latest LDA/Punjab building regulations and approved plan conditions."},
    "cda_islamabad": {"name": "CDA Islamabad (Concept)", "front": 10, "rear": 10, "side": 5, "coverage": 65, "parking": True, "notes": "Concept-level. CDA rules vary by zone/plot size; verify current CDA by-laws."},
    "sbca_karachi": {"name": "SBCA Karachi (Concept)", "front": 5, "rear": 5, "side": 3, "coverage": 70, "parking": True, "notes": "Concept-level. Verify SBCA Karachi Building & Town Planning Regulations for plot category."},
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
