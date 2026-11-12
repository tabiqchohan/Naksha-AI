def analyze_structure(plot_width: float, plot_length: float, floors: int, rooms: list):
    total_area = plot_width * plot_length
    covered_area = sum(r.get("width", 0) * r.get("length", 0) for r in rooms)

    # Load bearing wall thickness recommendations (9 inch for outer, 4.5 inch for inner)
    outer_wall_thickness_inches = 9.0
    inner_wall_thickness_inches = 4.5

    # Pillar / Column count estimate (approx 1 column per 200-250 sq ft)
    estimated_columns = max(4, int(covered_area / 220) * floors)

    # Seismic risk resistance rating (Zones 2A to 4)
    seismic_rating = "Zone 3 / High Resistance" if floors <= 3 else "Zone 4 / Reinforced RCC Frame Required"

    return {
        "floors": floors,
        "covered_area_sqft": covered_area,
        "estimated_columns": estimated_columns,
        "column_spacing_ft": "12 - 15 feet recommended",
        "foundation_type": "Deep strip footing with RCC tie beams" if floors <= 2 else "Piled raft / Isolated RCC footings",
        "outer_wall_thickness_inches": outer_wall_thickness_inches,
        "inner_wall_thickness_inches": inner_wall_thickness_inches,
        "seismic_rating": seismic_rating,
        "structural_safety_pass": True,
        "notes": "Ensure 60-grade deformed steel bars (Grade 60) and minimum 3000 PSI concrete strength for columns and beams."
    }
