from typing import List, Dict, Any
from app.models.schemas import Room, Plot, MaterialEstimate
from app.config import settings

class MaterialEstimator:
    @staticmethod
    def calculate_estimate(plot: Plot, rooms: List[Room], rate_per_sqft: float = 3200.0) -> MaterialEstimate:
        plot_total_sqft = plot.width * plot.length

        # Covered area calculation (excluding open lawn/OTS if labeled)
        covered_rooms = [r for r in rooms if r.type not in ["lawn", "ots_duct", "balcony"]]
        covered_area_sqft = sum(r.width * r.length for r in covered_rooms)

        # If no explicit rooms or covered area is 0, default to 75% of plot
        if covered_area_sqft <= 0:
            covered_area_sqft = plot_total_sqft * 0.75

        open_area_sqft = max(0.0, plot_total_sqft - covered_area_sqft)

        # Standard Civil Engineering Ratios (Pakistan & South Asia standards):
        # 1. Bricks: ~22 to 24 bricks per sqft covered area
        bricks_count = int(covered_area_sqft * 23.5)

        # 2. Cement: ~0.42 bags per sqft (OPC 50kg bags)
        cement_bags = int(covered_area_sqft * 0.42)

        # 3. Steel / Rebar: ~3.2 kg per sqft => converted to Metric Tons (1000 kg)
        steel_kg = covered_area_sqft * 3.2
        steel_tons = round(steel_kg / 1000.0, 2)

        # 4. Sand (Ravi / Chenab): ~1.8 cft per sqft
        sand_cft = round(covered_area_sqft * 1.8, 1)

        # 5. Crush / Gravel (Margalla/Sargodha): ~1.4 cft per sqft
        crush_cft = round(covered_area_sqft * 1.4, 1)

        # Cost Calculations
        total_pkr = round(covered_area_sqft * rate_per_sqft, 2)
        total_usd = round(total_pkr / settings.PKR_TO_USD_RATE, 2)

        breakdown = {
            "civil_grey_structure": {
                "bricks_cost_pkr": round(bricks_count * 15.0, 2), # ~Rs. 15 per Awwal brick
                "cement_cost_pkr": round(cement_bags * 1350.0, 2), # ~Rs. 1350 per bag
                "steel_cost_pkr": round(steel_kg * 260.0, 2),      # ~Rs. 260 per kg (60-grade)
                "sand_cost_pkr": round(sand_cft * 45.0, 2),
                "crush_cost_pkr": round(crush_cft * 115.0, 2),
            },
            "labor_and_supervision_pkr": round(covered_area_sqft * 550.0, 2),
            "plumbing_and_piping_pkr": round(covered_area_sqft * 180.0, 2),
            "electrical_conduit_pkr": round(covered_area_sqft * 140.0, 2),
            "unit_rates": {
                "rate_per_sqft_pkr": rate_per_sqft,
                "brick_unit_rate_pkr": 15.0,
                "cement_bag_rate_pkr": 1350.0,
                "steel_kg_rate_pkr": 260.0
            }
        }

        return MaterialEstimate(
            total_plot_sqft=round(plot_total_sqft, 1),
            covered_area_sqft=round(covered_area_sqft, 1),
            open_area_sqft=round(open_area_sqft, 1),
            bricks_count=bricks_count,
            cement_bags=cement_bags,
            steel_tons=steel_tons,
            sand_cft=sand_cft,
            crush_cft=crush_cft,
            estimated_cost_pkr=total_pkr,
            estimated_cost_usd=total_usd,
            breakdown=breakdown
        )
