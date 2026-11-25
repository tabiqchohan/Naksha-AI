import math
from typing import List, Dict, Any, Tuple, Optional
from app.models.cbm_schemas import CanonicalBuildingModel, WallSegment, RoomPolygon, Opening, BuildingLevel, StairFlight, RoofStructure
from app.services.geometry_validator import CBMGeometryValidator

class CBM3DGenerator:
    """Converts a CanonicalBuildingModel (CBM) into a parametric 3D scene representation for Three.js rendering."""

    @staticmethod
    def generate_3d_scene_payload(cbm: CanonicalBuildingModel) -> Dict[str, Any]:
        """Processes CBM data into optimized 3D primitives with deduplicated walls and openings."""
        # 1. Deduplicate walls using Phase 2 validator
        deduped_walls = CBMGeometryValidator.deduplicate_walls(cbm.walls)

        # 2. Map levels and elevations
        levels_data = []
        for lvl in cbm.levels:
            levels_data.append({
                "level_id": lvl.level_id,
                "index": lvl.index,
                "name": lvl.name,
                "elevation": lvl.elevation,
                "height": lvl.height,
                "slab_thickness": lvl.slab_thickness,
            })

        # 3. Process rooms (floors and ceilings)
        rooms_data = []
        for rp in cbm.rooms:
            rooms_data.append({
                "id": rp.id,
                "level_id": rp.level_id,
                "name": rp.name,
                "room_type": rp.room_type,
                "polygon": rp.polygon,
                "area_sqft": rp.area_sqft,
                "color": rp.color,
            })

        # 4. Process walls
        walls_data = []
        for w in deduped_walls:
            dx = w.end[0] - w.start[0]
            dy = w.end[1] - w.start[1]
            length = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            mid_x = (w.start[0] + w.end[0]) / 2.0
            mid_y = (w.start[1] + w.end[1]) / 2.0

            walls_data.append({
                "id": w.id,
                "level_id": w.level_id,
                "start": w.start,
                "end": w.end,
                "midpoint": (mid_x, mid_y),
                "length": round(length, 2),
                "angle": round(angle, 4),
                "thickness": w.thickness,
                "wall_type": w.wall_type,
                "material": w.material,
            })

        # 5. Process openings (doors/windows linked to walls)
        openings_data = []
        for op in cbm.openings:
            openings_data.append({
                "id": op.id,
                "wall_id": op.wall_id,
                "level_id": op.level_id,
                "opening_type": op.opening_type,
                "offset_from_start": op.offset_from_start,
                "width": op.width,
                "height": op.height,
                "sill_height": op.sill_height,
                "swing": op.swing,
            })

        # 6. Process stairs
        stairs_data = []
        for st in cbm.stairs:
            stairs_data.append({
                "id": st.id,
                "level_id": st.level_id,
                "target_level_id": st.target_level_id,
                "start_point": st.start_point,
                "end_point": st.end_point,
                "width": st.width,
                "riser_count": st.riser_count,
            })

        # 7. Process roof
        roof_data = None
        if cbm.roof:
            roof_data = {
                "id": cbm.roof.id,
                "roof_type": cbm.roof.roof_type,
                "overhang": cbm.roof.overhang,
                "pitch_angle": cbm.roof.pitch_angle,
            }

        return {
            "project_id": cbm.project_id,
            "title": cbm.title,
            "site": {
                "plot_width": cbm.site.plot_width,
                "plot_length": cbm.site.plot_length,
                "unit": cbm.site.unit,
                "setbacks": cbm.site.setbacks,
            },
            "levels": levels_data,
            "rooms": rooms_data,
            "walls": walls_data,
            "openings": openings_data,
            "stairs": stairs_data,
            "roof": roof_data,
            "material_estimate": cbm.material_estimate,
        }
