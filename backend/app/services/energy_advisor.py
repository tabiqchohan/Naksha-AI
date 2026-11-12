def calculate_energy_score(plot_width: float, plot_length: float, rooms: list, orientation: str = "North"):
    total_area = plot_width * plot_length
    covered_area = sum(r.get("width", 0) * r.get("length", 0) for r in rooms)
    open_area = max(0, total_area - covered_area)

    # Ventilation index based on open area ratio and windows
    open_ratio = open_area / total_area if total_area > 0 else 0.2
    ventilation_score = min(100, int(open_ratio * 120 + 40))

    # Solar gain / orientation efficiency
    solar_score = 85 if orientation in ["North", "East"] else 72

    # Carbon footprint estimation (kg CO2 equivalent for construction material)
    # Approx 350 kg CO2 per sq m of covered area
    covered_sqm = covered_area * 0.092903
    carbon_footprint_tons = round((covered_sqm * 320) / 1000, 2)

    overall_score = int((ventilation_score * 0.5) + (solar_score * 0.3) + (min(100, open_ratio * 200) * 0.2))

    return {
        "overall_score": overall_score,
        "ventilation_score": ventilation_score,
        "solar_efficiency": solar_score,
        "carbon_footprint_tons": carbon_footprint_tons,
        "green_rating": "A+" if overall_score >= 85 else ("A" if overall_score >= 75 else "B+"),
        "recommendations": [
            "Add double-glazed windows on west-facing facade to reduce heat gain.",
            "Install solar panels on rooftop (estimated 5kW capacity supported).",
            "Incorporate courtyard or indoor plants to enhance passive cooling."
        ]
    }
