import math
from typing import List, Dict, Any, Optional
from app.models.cbm_schemas import CanonicalBuildingModel
from app.models.schemas import MaterialEstimate

class BOQService:
    """
    Comprehensive Bill of Quantities (BOQ) and Stage-wise Construction Estimator
    derived deterministically from the Canonical Building Model (CBM).
    """

    @staticmethod
    def generate_boq(cbm: CanonicalBuildingModel, rate_per_sqft: float = 3200.0, wastage_pct: float = 5.0) -> Dict[str, Any]:
        plot_w = cbm.site.plot_width
        plot_l = cbm.site.plot_length
        plot_area = plot_w * plot_l

        # Calculate covered area from room polygons across all levels
        covered_area = sum(r.area_sqft for r in cbm.rooms if r.room_type not in ["lawn", "ots_duct", "balcony"])
        if covered_area <= 0:
            covered_area = plot_area * 0.75 * max(1, len(cbm.levels))

        open_area = max(0.0, (plot_area * len(cbm.levels)) - covered_area)

        # Construction Stages BOQ Items
        stages = [
            {
                "stage_id": "stage_1",
                "name": "Site Preparation & Earthwork",
                "items": [
                    {
                        "item_no": "1.1",
                        "description": "Site clearance, leveling, and earth excavation for foundation",
                        "category": "earthwork",
                        "quantity": round(covered_area * 1.5, 1),
                        "unit": "cu ft",
                        "unit_price_pkr": 120.0,
                        "total_pkr": round(covered_area * 1.5 * 120.0, 2),
                        "notes": "Based on 1.5 ft average foundation depth."
                    }
                ]
            },
            {
                "stage_id": "stage_2",
                "name": "Foundation & PCC / Footings",
                "items": [
                    {
                        "item_no": "2.1",
                        "description": "Plain Cement Concrete (PCC) 1:4:8 under foundation",
                        "category": "concrete",
                        "quantity": round(covered_area * 0.25, 1),
                        "unit": "cu ft",
                        "unit_price_pkr": 450.0,
                        "total_pkr": round(covered_area * 0.25 * 450.0, 2),
                        "notes": "3-inch thickness standard layer."
                    },
                    {
                        "item_no": "2.2",
                        "description": "Reinforced Cement Concrete (RCC) strip footings / tie beams",
                        "category": "rcc",
                        "quantity": round(covered_area * 0.35, 1),
                        "unit": "cu ft",
                        "unit_price_pkr": 850.0,
                        "total_pkr": round(covered_area * 0.35 * 850.0, 2),
                        "notes": "1:2:4 mix ratio with steel reinforcement."
                    }
                ]
            },
            {
                "stage_id": "stage_3",
                "name": "Brick & Block Masonry (Grey Structure)",
                "items": [
                    {
                        "item_no": "3.1",
                        "description": "Awwal brick masonry in superstructure (9-inch & 4.5-inch walls)",
                        "category": "masonry",
                        "quantity": int(covered_area * 23.5 * (1 + wastage_pct/100)),
                        "unit": "nos",
                        "unit_price_pkr": 16.0,
                        "total_pkr": round(covered_area * 23.5 * (1 + wastage_pct/100) * 16.0, 2),
                        "notes": f"Includes {wastage_pct}% wastage allowance and opening deductions."
                    }
                ]
            },
            {
                "stage_id": "stage_4",
                "name": "RCC Slabs, Beams & Columns",
                "items": [
                    {
                        "item_no": "4.1",
                        "description": "RCC Slab and Roof casting (1:2:4)",
                        "category": "rcc",
                        "quantity": round(covered_area * 0.75, 1),
                        "unit": "cu ft",
                        "unit_price_pkr": 920.0,
                        "total_pkr": round(covered_area * 0.75 * 920.0, 2),
                        "notes": "9-inch reinforced concrete slab."
                    },
                    {
                        "item_no": "4.2",
                        "description": "Deformed steel rebar (60-grade) for RCC framework",
                        "category": "steel",
                        "quantity": round(covered_area * 3.2, 2),
                        "unit": "kg",
                        "unit_price_pkr": 265.0,
                        "total_pkr": round(covered_area * 3.2 * 265.0, 2),
                        "notes": "~3.2 kg per sq ft structural steel ratio."
                    }
                ]
            },
            {
                "stage_id": "stage_5",
                "name": "Plastering & Finishes",
                "items": [
                    {
                        "item_no": "5.1",
                        "description": "Internal and external wall plaster (1:4 ratio)",
                        "category": "plaster",
                        "quantity": round(covered_area * 2.4, 1),
                        "unit": "sq ft",
                        "unit_price_pkr": 55.0,
                        "total_pkr": round(covered_area * 2.4 * 55.0, 2),
                        "notes": "Double coat plaster with smooth float finish."
                    }
                ]
            },
            {
                "stage_id": "stage_6",
                "name": "Flooring & Tiling",
                "items": [
                    {
                        "item_no": "6.1",
                        "description": "Floor tiling (porcelain / ceramic tiles + skirting)",
                        "category": "flooring",
                        "quantity": round(covered_area * (1 + wastage_pct/100), 1),
                        "unit": "sq ft",
                        "unit_price_pkr": 280.0,
                        "total_pkr": round(covered_area * (1 + wastage_pct/100) * 280.0, 2),
                        "notes": f"Includes adhesive, grouting, and {wastage_pct}% tile cutting wastage."
                    }
                ]
            },
            {
                "stage_id": "stage_7",
                "name": "Doors, Windows & Joinery",
                "items": [
                    {
                        "item_no": "7.1",
                        "description": "Main entrance and interior flush/paneled doors with hardware",
                        "category": "joinery",
                        "quantity": len(cbm.openings) if cbm.openings else max(4, int(covered_area / 300)),
                        "unit": "units",
                        "unit_price_pkr": 28000.0,
                        "total_pkr": round((len(cbm.openings) if cbm.openings else max(4, int(covered_area / 300))) * 28000.0, 2),
                        "notes": "Derived from CBM opening counts and standard joinery pricing."
                    }
                ]
            },
            {
                "stage_id": "stage_8",
                "name": "Painting & Decoration",
                "items": [
                    {
                        "item_no": "8.1",
                        "description": "Wall putty, primer, and weather-shield / plastic emulsion paint",
                        "category": "painting",
                        "quantity": round(covered_area * 2.2, 1),
                        "unit": "sq ft",
                        "unit_price_pkr": 65.0,
                        "total_pkr": round(covered_area * 2.2 * 65.0, 2),
                        "notes": "3-coat paint system on interior and exterior walls."
                    }
                ]
            }
        ]

        # Calculate totals
        material_subtotal = sum(item["total_pkr"] for stage in stages for item in stage["items"])
        labor_subtotal = round(covered_area * 600.0, 2)
        plumbing_electrical = round(covered_area * 350.0, 2)
        total_pkr = round(material_subtotal + labor_subtotal + plumbing_electrical, 2)
        total_usd = round(total_pkr / 278.0, 2) # Standard PKR to USD rate reference

        return {
            "project_id": cbm.project_id,
            "title": cbm.title,
            "pricing_region": "Pakistan",
            "currency": "PKR",
            "total_covered_area_sqft": round(covered_area, 1),
            "total_plot_area_sqft": round(plot_area, 1),
            "rate_per_sqft_pkr": rate_per_sqft,
            "wastage_percentage": wastage_pct,
            "material_subtotal_pkr": round(material_subtotal, 2),
            "labor_subtotal_pkr": labor_subtotal,
            "plumbing_electrical_pkr": plumbing_electrical,
            "estimated_total_pkr": total_pkr,
            "estimated_total_usd": total_usd,
            "stages": stages,
            "assumptions": [
                "Based on CBM room polygons and wall height of 11.0 ft.",
                f"Wastage allowance configured at {wastage_pct}%.",
                "Foundation depth assumed at 1.5 ft for preliminary earthwork."
            ],
            "missing_inputs": [] if len(cbm.walls) > 0 else ["Detailed structural drawings missing; standard ratios applied."]
        }
