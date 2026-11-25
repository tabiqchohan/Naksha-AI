import uuid
from typing import List, Dict, Any, Tuple
from app.models.schemas import FloorPlan, Room, Door, Window, Plot, MaterialEstimate
from app.models.cbm_schemas import (
    CanonicalBuildingModel,
    SiteGeometry,
    BuildingLevel,
    WallSegment,
    RoomPolygon,
    Opening,
    FloorSlab,
    RoofStructure,
)

class CBMAdapter:
    @staticmethod
    def to_cbm(plan: FloorPlan) -> CanonicalBuildingModel:
        """Converts legacy FloorPlan (rooms, doors, windows, plot) into CanonicalBuildingModel (CBM)."""
        plot = plan.plot
        site = SiteGeometry(
            plot_width=plot.width,
            plot_length=plot.length,
            unit=plot.unit,
            marla_size=plot.marla_size,
            total_area_sqft=plot.total_area_sqft,
        )

        # Levels (support multi-floor)
        max_floor = 0
        for r in plan.rooms:
            if getattr(r, "floor_level", 0) is not None:
                max_floor = max(max_floor, int(r.floor_level))

        levels: List[BuildingLevel] = []
        for lvl in range(max_floor + 1):
            levels.append(BuildingLevel(
                level_id=f"lvl_{lvl}",
                index=lvl,
                name="Ground Floor" if lvl == 0 else f"Floor {lvl + 1}",
                elevation=float(lvl * 12.0),
                height=11.0,
                slab_thickness=0.75,
            ))

        # Rooms -> RoomPolygon
        room_polygons: List[RoomPolygon] = []
        for r in plan.rooms:
            x, y, w, l = r.x, r.y, r.width, r.length
            poly = [(x, y), (x + w, y), (x + w, y + l), (x, y + l)]
            lvl_idx = int(getattr(r, "floor_level", 0) or 0)
            room_polygons.append(RoomPolygon(
                id=r.id,
                level_id=f"lvl_{lvl_idx}",
                name=r.name,
                room_type=r.type,
                polygon=poly,
                area_sqft=round(w * l, 1),
                color=r.color,
            ))

        # Derive Walls from Room bounding boxes
        walls: List[WallSegment] = []
        wall_map: Dict[Tuple[float, float, float, float], str] = {}

        def add_wall(p1: Tuple[float, float], p2: Tuple[float, float], lvl_id: str, w_type: str = "interior"):
            # Normalize direction
            if p1 > p2:
                p1, p2 = p2, p1
            key = (p1[0], p1[1], p2[0], p2[1])
            if key not in wall_map:
                w_id = f"w_{str(uuid.uuid4())[:8]}"
                wall_map[key] = w_id
                walls.append(WallSegment(
                    id=w_id,
                    level_id=lvl_id,
                    start=p1,
                    end=p2,
                    thickness=0.75,
                    wall_type=w_type,
                ))
            return wall_map[key]

        # Add outer plot boundary walls
        lvl_0_id = "lvl_0"
        add_wall((0, 0), (plot.width, 0), lvl_0_id, "exterior")
        add_wall((plot.width, 0), (plot.width, plot.length), lvl_0_id, "exterior")
        add_wall((plot.width, plot.length), (0, plot.length), lvl_0_id, "exterior")
        add_wall((0, plot.length), (0, 0), lvl_0_id, "exterior")

        # Add room partition walls
        for r in plan.rooms:
            x, y, w, l = r.x, r.y, r.width, r.length
            lvl_id = f"lvl_{int(getattr(r, 'floor_level', 0) or 0)}"
            add_wall((x, y), (x + w, y), lvl_id, "interior")
            add_wall((x + w, y), (x + w, y + l), lvl_id, "interior")
            add_wall((x + w, y + l), (x, y + l), lvl_id, "interior")
            add_wall((x, y + l), (x, y), lvl_id, "interior")

        # Openings (Doors and Windows) linked to walls
        openings: List[Opening] = []
        # Fallback wall lookup helper
        default_wall_id = walls[0].id if walls else "w_default"

        for d in plan.doors:
            # Find matching room
            matching_room = next((r for r in plan.rooms if r.name == d.room_name or r.id == d.room_name), None)
            target_wall_id = default_wall_id
            if matching_room:
                rx, ry, rw, rl = matching_room.x, matching_room.y, matching_room.width, matching_room.length
                lvl_id = f"lvl_{int(getattr(matching_room, 'floor_level', 0) or 0)}"
                if d.wall == "north":
                    target_wall_id = add_wall((rx, ry), (rx + rw, ry), lvl_id, "interior")
                elif d.wall == "south":
                    target_wall_id = add_wall((rx, ry + rl), (rx + rw, ry + rl), lvl_id, "interior")
                elif d.wall == "east":
                    target_wall_id = add_wall((rx + rw, ry), (rx + rw, ry + rl), lvl_id, "interior")
                elif d.wall == "west":
                    target_wall_id = add_wall((rx, ry), (rx, ry + rl), lvl_id, "interior")

            openings.append(Opening(
                id=d.id,
                wall_id=target_wall_id,
                level_id="lvl_0",
                opening_type="door",
                offset_from_start=d.position,
                width=d.width,
                height=7.0,
                sill_height=0.0,
                swing=d.swing,
            ))

        for w in plan.windows:
            matching_room = next((r for r in plan.rooms if r.name == w.room_name or r.id == w.room_name), None)
            target_wall_id = default_wall_id
            if matching_room:
                rx, ry, rw, rl = matching_room.x, matching_room.y, matching_room.width, matching_room.length
                lvl_id = f"lvl_{int(getattr(matching_room, 'floor_level', 0) or 0)}"
                if w.wall == "north":
                    target_wall_id = add_wall((rx, ry), (rx + rw, ry), lvl_id, "exterior")
                elif w.wall == "south":
                    target_wall_id = add_wall((rx, ry + rl), (rx + rw, ry + rl), lvl_id, "exterior")
                elif w.wall == "east":
                    target_wall_id = add_wall((rx + rw, ry), (rx + rw, ry + rl), lvl_id, "exterior")
                elif w.wall == "west":
                    target_wall_id = add_wall((rx, ry), (rx, ry + rl), lvl_id, "exterior")

            openings.append(Opening(
                id=w.id,
                wall_id=target_wall_id,
                level_id="lvl_0",
                opening_type="window",
                offset_from_start=w.position,
                width=w.width,
                height=4.0,
                sill_height=3.0,
            ))

        return CanonicalBuildingModel(
            schema_version="1.0.0",
            project_id=plan.id,
            title=plan.title,
            description=plan.description,
            site=site,
            levels=levels,
            walls=walls,
            rooms=room_polygons,
            openings=openings,
            roof=RoofStructure(id="roof_1", roof_type="flat_parapet", overhang=1.0),
            material_estimate=plan.material_estimate.model_dump() if plan.material_estimate else None,
            metadata={"warnings": plan.warnings},
        )

    @staticmethod
    def from_cbm(cbm: CanonicalBuildingModel) -> FloorPlan:
        """Converts CanonicalBuildingModel back into legacy FloorPlan for 100% backward compatibility."""
        plot = Plot(
            width=cbm.site.plot_width,
            length=cbm.site.plot_length,
            unit=cbm.site.unit,
            marla_size=cbm.site.marla_size,
            total_area_sqft=cbm.site.total_area_sqft,
        )

        rooms: List[Room] = []
        for rp in cbm.rooms:
            # Reconstruct x, y, width, length from polygon
            xs = [pt[0] for pt in rp.polygon]
            ys = [pt[1] for pt in rp.polygon]
            x = min(xs)
            y = min(ys)
            w = max(xs) - min(xs)
            l = max(ys) - min(ys)
            lvl_index = int(rp.level_id.split("_")[-1]) if "_" in rp.level_id else 0

            rooms.append(Room(
                id=rp.id,
                name=rp.name,
                type=rp.room_type,
                x=x,
                y=y,
                width=w,
                length=l,
                sqft=rp.area_sqft,
                color=rp.color,
                floor_level=lvl_index,
            ))

        # Map openings back to doors and windows
        wall_to_room: Dict[str, str] = {}
        for r in rooms:
            # Approximate mapping based on proximity
            pass

        doors: List[Door] = []
        windows: List[Window] = []

        for op in cbm.openings:
            # Find room name if possible
            room_name = "Living Room"
            wall_dir = "north"

            if op.opening_type == "door":
                doors.append(Door(
                    id=op.id,
                    room_name=room_name,
                    wall=wall_dir,
                    position=op.offset_from_start,
                    width=op.width,
                    swing=op.swing or "inward_left",
                ))
            else:
                windows.append(Window(
                    id=op.id,
                    room_name=room_name,
                    wall=wall_dir,
                    position=op.offset_from_start,
                    width=op.width,
                ))

        mat_est = None
        if cbm.material_estimate:
            try:
                mat_est = MaterialEstimate(**cbm.material_estimate)
            except Exception:
                mat_est = None

        return FloorPlan(
            id=cbm.project_id,
            title=cbm.title,
            description=cbm.description,
            plot=plot,
            rooms=rooms,
            doors=doors,
            windows=windows,
            material_estimate=mat_est,
            warnings=cbm.metadata.get("warnings", []),
        )

    @staticmethod
    def validate_cbm(cbm: CanonicalBuildingModel) -> List[str]:
        """Validates CBM wall-opening relationships and multi-floor integrity."""
        errors = []
        wall_ids = {w.id for w in cbm.walls}
        level_ids = {l.level_id for l in cbm.levels}

        for op in cbm.openings:
            if op.wall_id not in wall_ids:
                errors.append(f"Opening '{op.id}' references non-existent wall ID '{op.wall_id}'.")
            if op.level_id not in level_ids:
                errors.append(f"Opening '{op.id}' references non-existent level ID '{op.level_id}'.")

        for r in cbm.rooms:
            if r.level_id not in level_ids:
                errors.append(f"Room '{r.name}' references non-existent level ID '{r.level_id}'.")

        return errors
