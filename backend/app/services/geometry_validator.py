import math
import uuid
from typing import List, Dict, Any, Tuple, Optional
from shapely.geometry import Polygon, LineString, box, MultiPolygon
from shapely.ops import unary_union, polygonize
from shapely.validation import explain_validity
from pydantic import BaseModel
from app.models.cbm_schemas import (
    CanonicalBuildingModel,
    RoomPolygon,
    WallSegment,
    Opening,
    BuildingLevel,
    SiteGeometry,
    StairFlight,
)
from app.models.schemas import Room, Plot, FurnitureItem

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    score: float = 100.0
    details: Dict[str, Any] = {}

class GeometryValidator:
    """Legacy and service compatibility validator for floor plan generation and auto-arrangement."""

    @staticmethod
    def validate_and_correct_layout(plot: Plot, rooms: List[Room], road_facing: str = "north") -> Tuple[List[Room], List[str]]:
        """Validates and clamps room coordinates to plot boundaries."""
        warnings = []
        corrected_rooms = []
        for r in rooms:
            if r.x < 0:
                r.x = 0
                warnings.append(f"Room '{r.name}' x adjusted to 0.")
            if r.y < 0:
                r.y = 0
                warnings.append(f"Room '{r.name}' y adjusted to 0.")
            if r.x + r.width > plot.width:
                r.width = max(5.0, plot.width - r.x)
                warnings.append(f"Room '{r.name}' width clamped to fit plot width ({plot.width} ft).")
            if r.y + r.length > plot.length:
                r.length = max(5.0, plot.length - r.y)
                warnings.append(f"Room '{r.name}' length clamped to fit plot length ({plot.length} ft).")
            r.sqft = round(r.width * r.length, 1)
            corrected_rooms.append(r)
        return corrected_rooms, warnings

    @staticmethod
    def auto_arrange_furniture(rooms: List[Room]) -> List[Room]:
        """Automatically arranges default furniture in rooms based on room type."""
        for r in rooms:
            if not getattr(r, "furniture", None) or len(r.furniture) == 0:
                r.furniture = []
                r_type = (r.type or "").lower()
                if "bed" in r_type or "master" in r_type:
                    r.furniture.append(FurnitureItem(
                        id=f"furn_{uuid.uuid4().hex[:6]}",
                        name="Bed",
                        type="bed",
                        x=max(0.5, r.width / 2 - 2.5),
                        y=max(0.5, r.length / 2 - 3.0),
                        width=5.0,
                        length=6.0
                    ))
                elif "living" in r_type or "lounge" in r_type or "drawing" in r_type:
                    r.furniture.append(FurnitureItem(
                        id=f"furn_{uuid.uuid4().hex[:6]}",
                        name="Sofa Set",
                        type="sofa",
                        x=max(0.5, r.width / 2 - 3.0),
                        y=max(0.5, r.length / 2 - 2.0),
                        width=6.0,
                        length=3.0
                    ))
                elif "kitchen" in r_type:
                    r.furniture.append(FurnitureItem(
                        id=f"furn_{uuid.uuid4().hex[:6]}",
                        name="Counter",
                        type="kitchen_counter",
                        x=0.5,
                        y=0.5,
                        width=max(2.0, r.width - 1.0),
                        length=2.0
                    ))
        return rooms


class CBMGeometryValidator:
    TOLERANCE = 1e-3  # 0.001 feet tolerance

    @staticmethod
    def validate_polygon_geometry(poly_coords: List[Tuple[float, float]]) -> Tuple[bool, str, float]:
        """Validates polygon vertices: non-self-intersecting, valid area, simple polygon."""
        if len(poly_coords) < 3:
            return False, "Polygon must have at least 3 vertices.", 0.0

        try:
            poly = Polygon(poly_coords)
            if not poly.is_valid:
                validity_msg = explain_validity(poly)
                return False, f"Polygon is self-intersecting or topologically invalid: {validity_msg}", 0.0

            if poly.geom_type != "Polygon":
                return False, f"Invalid geometry type: {poly.geom_type}", 0.0

            area = poly.area
            if area <= CBMGeometryValidator.TOLERANCE:
                return False, "Polygon area is zero or near-zero.", 0.0

            return True, "", round(area, 2)
        except Exception as e:
            return False, f"Geometry parsing error: {str(e)}", 0.0

    @staticmethod
    def validate_site_setbacks(site: SiteGeometry, room_polygons: List[RoomPolygon]) -> List[str]:
        """Validates that room polygons fall within plot boundaries."""
        errors = []
        plot_box = box(0, 0, site.plot_width, site.plot_length)

        for rp in room_polygons:
            try:
                poly = Polygon(rp.polygon)
                if not plot_box.covers(poly):
                    errors.append(f"Room '{rp.name}' (ID: {rp.id}) extends outside plot boundaries ({site.plot_width}x{site.plot_length} ft).")
            except Exception as e:
                errors.append(f"Error validating setbacks for room '{rp.name}': {str(e)}")

        return errors

    @staticmethod
    def detect_room_overlaps(room_polygons: List[RoomPolygon]) -> List[str]:
        """Detects overlapping rooms on the same floor level."""
        errors = []
        level_rooms: Dict[str, List[RoomPolygon]] = {}
        for rp in room_polygons:
            level_rooms.setdefault(rp.level_id, []).append(rp)

        for lvl_id, rooms in level_rooms.items():
            for i in range(len(rooms)):
                for j in range(i + 1, len(rooms)):
                    r1, r2 = rooms[i], rooms[j]
                    try:
                        p1 = Polygon(r1.polygon)
                        p2 = Polygon(r2.polygon)
                        intersection = p1.intersection(p2)
                        if not intersection.is_empty and intersection.area > CBMGeometryValidator.TOLERANCE:
                            errors.append(f"Room overlap detected between '{r1.name}' ({r1.id}) and '{r2.name}' ({r2.id}) on level '{lvl_id}' (overlap area: {round(intersection.area, 2)} sqft).")
                    except Exception as e:
                        errors.append(f"Error checking overlap between '{r1.name}' and '{r2.name}': {str(e)}")

        return errors

    @staticmethod
    def deduplicate_walls(walls: List[WallSegment]) -> List[WallSegment]:
        """Deduplicates overlapping or redundant wall segments, merging collinear shared walls."""
        wall_map: Dict[Tuple[float, float, float, float], WallSegment] = {}

        for w in walls:
            p1, p2 = w.start, w.end
            if p1 > p2:
                p1, p2 = p2, p1
            key = (round(p1[0], 2), round(p1[1], 2), round(p2[0], 2), round(p2[1], 2))

            if key in wall_map:
                existing = wall_map[key]
                if w.wall_type == "exterior" and existing.wall_type != "exterior":
                    wall_map[key] = w
            else:
                wall_map[key] = WallSegment(
                    id=w.id,
                    level_id=w.level_id,
                    start=p1,
                    end=p2,
                    thickness=w.thickness,
                    wall_type=w.wall_type,
                    material=w.material,
                )

        return list(wall_map.values())

    @staticmethod
    def validate_openings(openings: List[Opening], walls: List[WallSegment], levels: List[BuildingLevel]) -> List[str]:
        """Validates that openings reference valid walls and fit within wall lengths."""
        errors = []
        wall_dict = {w.id: w for w in walls}
        level_ids = {l.level_id for l in levels}

        for op in openings:
            if op.level_id not in level_ids:
                errors.append(f"Opening '{op.id}' references non-existent level ID '{op.level_id}'.")

            if op.wall_id not in wall_dict:
                errors.append(f"Opening '{op.id}' references non-existent wall ID '{op.wall_id}'.")
            else:
                wall = wall_dict[op.wall_id]
                dx = wall.end[0] - wall.start[0]
                dy = wall.end[1] - wall.start[1]
                wall_length = math.hypot(dx, dy)

                if op.offset_from_start < 0:
                    errors.append(f"Opening '{op.id}' offset ({op.offset_from_start}) cannot be negative.")
                if op.offset_from_start + op.width > wall_length + CBMGeometryValidator.TOLERANCE:
                    errors.append(f"Opening '{op.id}' exceeds host wall '{wall.id}' length (Wall length: {round(wall_length, 2)} ft, Opening span: {op.offset_from_start} to {op.offset_from_start + op.width} ft).")

        return errors

    @staticmethod
    def validate_stairs(stairs: List[StairFlight], levels: List[BuildingLevel]) -> List[str]:
        """Validates stair connections between valid levels."""
        errors = []
        level_dict = {l.level_id: l for l in levels}

        for stair in stairs:
            if stair.level_id not in level_dict:
                errors.append(f"Stair '{stair.id}' references non-existent start level ID '{stair.level_id}'.")
            if stair.target_level_id not in level_dict:
                errors.append(f"Stair '{stair.id}' references non-existent target level ID '{stair.target_level_id}'.")
            if stair.width < 2.5:
                errors.append(f"Stair '{stair.id}' width ({stair.width} ft) is below minimum building code (2.5 ft).")

        return errors

    @staticmethod
    def validate_room_constraints(room_polygons: List[RoomPolygon]) -> List[str]:
        """Validates room dimensions against architectural constraints (min width/length/area)."""
        errors = []
        MIN_AREA = 30.0  # sqft
        MIN_DIMENSION = 5.0  # feet

        for rp in room_polygons:
            if rp.area_sqft < MIN_AREA:
                errors.append(f"Room '{rp.name}' (ID: {rp.id}) area ({rp.area_sqft} sqft) is below minimum limit ({MIN_AREA} sqft).")

            xs = [pt[0] for pt in rp.polygon]
            ys = [pt[1] for pt in rp.polygon]
            w = max(xs) - min(xs)
            l = max(ys) - min(ys)

            if w < MIN_DIMENSION or l < MIN_DIMENSION:
                errors.append(f"Room '{rp.name}' (ID: {rp.id}) dimensions ({round(w, 1)}x{round(l, 1)} ft) violate minimum dimension constraint ({MIN_DIMENSION} ft).")

        return errors


class CBMValidationPipeline:
    @staticmethod
    def run_validation(cbm: CanonicalBuildingModel) -> ValidationResult:
        """Runs the complete Phase 2 architectural constraint and geometry validation pipeline."""
        errors: List[str] = []
        warnings: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Room polygon geometry & area checks
        valid_rooms = []
        for rp in cbm.rooms:
            valid, err, calc_area = CBMGeometryValidator.validate_polygon_geometry(rp.polygon)
            if not valid:
                errors.append(f"Room '{rp.name}' ({rp.id}): {err}")
            else:
                if abs(calc_area - rp.area_sqft) > 5.0:
                    warnings.append(f"Room '{rp.name}' stated area ({rp.area_sqft}) differs from calculated polygon area ({calc_area}).")
                valid_rooms.append(rp)

        # 2. Room constraints (min width, length, area)
        room_constraint_errors = CBMGeometryValidator.validate_room_constraints(cbm.rooms)
        errors.extend(room_constraint_errors)

        # 3. Room overlap detection
        overlap_errors = CBMGeometryValidator.detect_room_overlaps(cbm.rooms)
        errors.extend(overlap_errors)

        # 4. Site & Setback validation
        setback_errors = CBMGeometryValidator.validate_site_setbacks(cbm.site, cbm.rooms)
        errors.extend(setback_errors)

        # 5. Wall deduplication & validation
        deduped_walls = CBMGeometryValidator.deduplicate_walls(cbm.walls)
        details["original_wall_count"] = len(cbm.walls)
        details["deduplicated_wall_count"] = len(deduped_walls)

        # 6. Openings validation
        opening_errors = CBMGeometryValidator.validate_openings(cbm.openings, deduped_walls, cbm.levels)
        errors.extend(opening_errors)

        # 7. Stair validation
        stair_errors = CBMGeometryValidator.validate_stairs(cbm.stairs, cbm.levels)
        errors.extend(stair_errors)

        score = max(0.0, 100.0 - (len(errors) * 15.0) - (len(warnings) * 5.0))
        is_valid = len(errors) == 0

        details["error_count"] = len(errors)
        details["warning_count"] = len(warnings)
        details["tested_rooms"] = len(cbm.rooms)
        details["tested_walls"] = len(deduped_walls)
        details["tested_openings"] = len(cbm.openings)

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            score=round(score, 1),
            details=details,
        )
