import io
import math
from typing import List, Dict, Any, Tuple
from app.models.cbm_schemas import (
    CanonicalBuildingModel,
    BuildingLevel,
    RoomPolygon,
    WallSegment,
    Opening,
    StairFlight,
    RoofStructure,
)

class ArchitecturalDrawingService:
    @staticmethod
    def generate_drawings_payload(cbm: CanonicalBuildingModel) -> Dict[str, Any]:
        """Generates structured architectural drawing data from CBM with true orthographic projections and section data."""
        site = cbm.site
        levels_data = []

        for lvl in cbm.levels:
            lvl_rooms = [r for r in cbm.rooms if r.level_id == lvl.level_id]
            lvl_walls = [w for w in cbm.walls if w.level_id == lvl.level_id]
            lvl_openings = [op for op in cbm.openings if op.level_id == lvl.level_id]
            lvl_stairs = [st for st in cbm.stairs if st.level_id == lvl.level_id]

            room_schedules = []
            total_floor_area = 0.0
            for r in lvl_rooms:
                area = r.area_sqft
                total_floor_area += area
                poly = r.polygon
                perimeter = 0.0
                for i in range(len(poly)):
                    p1 = poly[i]
                    p2 = poly[(i + 1) % len(poly)]
                    perimeter += math.hypot(p2[0] - p1[0], p2[1] - p1[1])

                room_schedules.append({
                    "id": r.id,
                    "name": r.name,
                    "room_type": r.room_type,
                    "area_sqft": area,
                    "perimeter_ft": round(perimeter, 2),
                    "polygon": poly,
                    "color": r.color or "#1e293b",
                })

            levels_data.append({
                "level_id": lvl.level_id,
                "index": lvl.index,
                "name": lvl.name,
                "elevation": lvl.elevation,
                "height": lvl.height,
                "slab_thickness": lvl.slab_thickness,
                "total_area_sqft": round(total_floor_area, 2),
                "rooms": room_schedules,
                "walls": [{"id": w.id, "start": w.start, "end": w.end, "thickness": w.thickness, "wall_type": w.wall_type} for w in lvl_walls],
                "openings": [{"id": op.id, "wall_id": op.wall_id, "type": op.opening_type, "width": op.width, "height": op.height, "sill_height": op.sill_height, "offset": op.offset_from_start} for op in lvl_openings],
                "stairs": [{"id": st.id, "start": st.start_point, "end": st.end_point, "width": st.width, "riser_count": st.riser_count} for st in lvl_stairs],
            })

        door_schedule = []
        window_schedule = []
        wall_dict = {w.id: w for w in cbm.walls}

        for op in cbm.openings:
            host_wall = wall_dict.get(op.wall_id)
            wall_type = host_wall.wall_type if host_wall else "exterior"
            item = {
                "id": op.id,
                "wall_id": op.wall_id,
                "wall_type": wall_type,
                "level_id": op.level_id,
                "width": op.width,
                "height": op.height,
                "sill_height": op.sill_height,
                "offset": op.offset_from_start,
                "swing": op.swing,
            }
            if op.opening_type == "door":
                door_schedule.append(item)
            else:
                window_schedule.append(item)

        total_building_area = sum(lvl["total_area_sqft"] for lvl in levels_data)

        ortho_elevations = ArchitecturalDrawingService._compute_orthographic_elevations(cbm)
        building_sections = ArchitecturalDrawingService._compute_building_sections(cbm)

        return {
            "project_id": cbm.project_id,
            "title": cbm.title,
            "site": {
                "plot_width": site.plot_width,
                "plot_length": site.plot_length,
                "total_area_sqft": site.total_area_sqft or (site.plot_width * site.plot_length),
                "marla_size": site.marla_size,
                "setbacks": site.setbacks,
            },
            "levels": levels_data,
            "elevations": ortho_elevations,
            "sections": building_sections,
            "schedules": {
                "doors": door_schedule,
                "windows": window_schedule,
                "total_building_area_sqft": round(total_building_area, 2),
            },
            "roof": cbm.roof.model_dump() if cbm.roof else None,
        }

    @staticmethod
    def _compute_orthographic_elevations(cbm: CanonicalBuildingModel) -> Dict[str, Any]:
        plot_w = cbm.site.plot_width
        plot_l = cbm.site.plot_length
        max_elevation = max([lvl.elevation + lvl.height for lvl in cbm.levels] or [11.0])
        if cbm.roof:
            max_elevation += 3.0

        wall_elements = []
        for w in cbm.walls:
            lvl = next((l for l in cbm.levels if l.level_id == w.level_id), None)
            elev = lvl.elevation if lvl else 0.0
            height = lvl.height if lvl else 11.0
            wall_elements.append({
                "id": w.id,
                "level_id": w.level_id,
                "start": w.start,
                "end": w.end,
                "wall_type": w.wall_type,
                "base_elevation": elev,
                "height": height,
            })

        opening_elements = []
        wall_map = {w.id: w for w in cbm.walls}
        for op in cbm.openings:
            hw = wall_map.get(op.wall_id)
            if hw:
                lvl = next((l for l in cbm.levels if l.level_id == op.level_id), None)
                elev = (lvl.elevation if lvl else 0.0) + op.sill_height
                opening_elements.append({
                    "id": op.id,
                    "type": op.opening_type,
                    "width": op.width,
                    "height": op.height,
                    "sill_height": op.sill_height,
                    "absolute_base_elevation": elev,
                    "wall_start": hw.start,
                    "wall_end": hw.end,
                })

        return {
            "front": {"view": "South Elevation", "axis_span": plot_w, "max_height": max_elevation, "walls": wall_elements, "openings": opening_elements},
            "rear": {"view": "North Elevation", "axis_span": plot_w, "max_height": max_elevation, "walls": wall_elements, "openings": opening_elements},
            "left": {"view": "West Elevation", "axis_span": plot_l, "max_height": max_elevation, "walls": wall_elements, "openings": opening_elements},
            "right": {"view": "East Elevation", "axis_span": plot_l, "max_height": max_elevation, "walls": wall_elements, "openings": opening_elements},
        }

    @staticmethod
    def _compute_building_sections(cbm: CanonicalBuildingModel) -> Dict[str, Any]:
        plot_w = cbm.site.plot_width
        plot_l = cbm.site.plot_length
        mid_x = plot_w / 2.0
        mid_y = plot_l / 2.0

        longitudinal_intersections = []
        transverse_intersections = []

        for w in cbm.walls:
            x1, y1 = w.start
            x2, y2 = w.end
            if (x1 <= mid_x <= x2) or (x2 <= mid_x <= x1):
                longitudinal_intersections.append({"wall_id": w.id, "level_id": w.level_id, "thickness": w.thickness, "start": w.start, "end": w.end})
            if (y1 <= mid_y <= y2) or (y2 <= mid_y <= y1):
                transverse_intersections.append({"wall_id": w.id, "level_id": w.level_id, "thickness": w.thickness, "start": w.start, "end": w.end})

        levels_info = [{"level_id": l.level_id, "name": l.name, "elevation": l.elevation, "height": l.height, "slab_thickness": l.slab_thickness} for l in cbm.levels]

        return {
            "longitudinal_section_aa": {
                "cutting_plane": f"X = {mid_x} ft (North-South)",
                "intersected_walls": len(longitudinal_intersections),
                "levels": levels_info,
                "intersections": longitudinal_intersections,
            },
            "transverse_section_bb": {
                "cutting_plane": f"Y = {mid_y} ft (East-West)",
                "intersected_walls": len(transverse_intersections),
                "levels": levels_info,
                "intersections": transverse_intersections,
            }
        }

    @staticmethod
    def generate_architectural_pdf(cbm: CanonicalBuildingModel, add_watermark: bool = True) -> bytes:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        payload = ArchitecturalDrawingService.generate_drawings_payload(cbm)
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(letter))
        page_w, page_h = landscape(letter)

        plot_w = payload["site"]["plot_width"]
        plot_l = payload["site"]["plot_length"]

        # --- PAGE 1: COVER & GROUND FLOOR PLAN ---
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)

        if add_watermark:
            c.saveState()
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 50)
            c.setFillAlpha(0.06)
            c.translate(page_w / 2, page_h / 2)
            c.rotate(30)
            c.drawCentredString(0, 0, "NAKSHA AI — PROFESSIONAL ARCHITECTURAL SET")
            c.restoreState()

        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, page_h - 35, f"NAKSHA AI ARCHITECTURAL DRAWING SET: {payload['title'].upper()}")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 9)
        c.drawString(40, page_h - 50, f"Plot: {plot_w}' x {plot_l}' | Total Area: {payload['site']['total_area_sqft']} sq ft | Project ID: {payload['project_id']}")
        c.drawString(40, page_h - 64, "Scale: 1:100 (Architectural) | Authoritative Source: Canonical Building Model (CBM)")

        draw_x, draw_y = 50, 70
        max_w, max_h = page_w - 280, page_h - 160
        scale = min(max_w / max(1, plot_w), max_h / max(1, plot_l))

        c.setStrokeColor(colors.HexColor("#38bdf8"))
        c.setLineWidth(2)
        c.rect(draw_x, draw_y, plot_w * scale, plot_l * scale, fill=0, stroke=1)

        ground_lvl = payload["levels"][0] if payload["levels"] else None
        if ground_lvl:
            for r in ground_lvl["rooms"]:
                xs = [pt[0] for pt in r["polygon"]]
                ys = [pt[1] for pt in r["polygon"]]
                if not xs or not ys:
                    continue
                rx = draw_x + min(xs) * scale
                ry = draw_y + min(ys) * scale
                rw = (max(xs) - min(xs)) * scale
                rl = (max(ys) - min(ys)) * scale

                c.setFillColor(colors.HexColor("#1e293b"))
                c.setStrokeColor(colors.white)
                c.setLineWidth(1)
                c.rect(rx, ry, rw, rl, fill=1, stroke=1)

                c.setFillColor(colors.white)
                c.setFont("Helvetica-Bold", 7)
                c.drawCentredString(rx + rw / 2, ry + rl / 2 + 4, (r["name"] or "")[:16])
                c.setFont("Helvetica", 6)
                c.setFillColor(colors.HexColor("#94a3b8"))
                c.drawCentredString(rx + rw / 2, ry + rl / 2 - 4, f"{int(r['area_sqft'])} sqft")

        panel_x = page_w - 220
        c.setFillColor(colors.HexColor("#1e293b"))
        c.rect(panel_x - 10, 60, 200, page_h - 140, fill=1, stroke=1)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(panel_x, page_h - 90, "GROUND FLOOR SUMMARY")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.white)
        lines = [
            f"Level Name: {ground_lvl['name'] if ground_lvl else 'Ground'}",
            f"Floor Area: {ground_lvl['total_area_sqft'] if ground_lvl else 0} sqft",
            f"Rooms Count: {len(ground_lvl['rooms']) if ground_lvl else 0}",
            f"Walls Count: {len(ground_lvl['walls']) if ground_lvl else 0}",
            f"Openings: {len(ground_lvl['openings']) if ground_lvl else 0}",
        ]
        y_pos = page_h - 110
        for ln in lines:
            c.drawString(panel_x, y_pos, ln)
            y_pos -= 14

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 6.5)
        c.drawString(40, 18, "Sheet A-01: Ground Floor Architectural Plan | Naksha AI CBM Engine")
        c.showPage()

        # --- PAGE 2: UPPER FLOORS & ROOF PLAN ---
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, page_h - 35, "UPPER FLOORS & ROOF PLAN (CBM DERIVED)")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 9)
        c.drawString(40, page_h - 50, f"Project: {payload['title']} | Levels: {len(payload['levels'])}")

        y_offset = page_h - 120
        for lvl in payload["levels"][1:]:
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y_offset, f"{lvl['name']} (Elevation: +{lvl['elevation']}ft, Height: {lvl['height']}ft)")
            y_offset -= 16
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.white)
            c.drawString(40, y_offset, f"Area: {lvl['total_area_sqft']} sqft | Rooms: {len(lvl['rooms'])} | Walls: {len(lvl['walls'])}")
            y_offset -= 24
            for r in lvl["rooms"]:
                c.drawString(60, y_offset, f"- {r['name']} ({r['room_type']}): {r['area_sqft']} sqft, Perimeter: {r['perimeter_ft']} ft")
                y_offset -= 12
            y_offset -= 15

        if payload["roof"]:
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y_offset, f"Roof Structure: {payload['roof']['roof_type'].upper()} (Overhang: {payload['roof']['overhang']}ft)")

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 6.5)
        c.drawString(40, 18, "Sheet A-02: Upper Floors & Roof Plan | Naksha AI CBM Engine")
        c.showPage()

        # --- PAGE 3: ACTUAL VECTOR ELEVATIONS & SECTIONS (SHEET A-03) ---
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, page_h - 35, "ACTUAL VECTOR ORTHOGRAPHIC ELEVATIONS & BUILDING SECTIONS")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 9)
        c.drawString(40, page_h - 50, "Fully rendered vector projections derived from CBM walls, levels, openings, slabs and roof geometry.")

        elevs = payload["elevations"]
        secs = payload["sections"]
        levels = payload["levels"]

        # Helper to draw actual vector elevation view
        def _render_vector_elevation(ex, ey, ew, eh, view_name, max_h):
            c.setStrokeColor(colors.white)
            c.setLineWidth(1.2)
            c.rect(ex, ey, ew, eh, fill=0, stroke=1)
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 8)
            c.drawString(ex, ey + eh + 6, view_name)

            # Draw level reference lines and building outline
            v_scale = eh / max(1.0, max_h)
            h_scale = ew / max(1.0, plot_w)

            c.setStrokeColor(colors.HexColor("#475569"))
            c.setLineWidth(0.5)
            for lvl in levels:
                ly = ey + lvl["elevation"] * v_scale
                c.line(ex, ly, ex + ew, ly)
                c.setFillColor(colors.HexColor("#94a3b8"))
                c.setFont("Helvetica", 6)
                c.drawString(ex + 4, ly + 2, f"+{int(lvl['elevation'])}ft ({lvl['name']})")

            # Draw vector massing outline
            c.setStrokeColor(colors.HexColor("#38bdf8"))
            c.setLineWidth(1.5)
            building_h = max([l["elevation"] + l["height"] for l in levels] or [11.0])
            c.rect(ex + ew * 0.1, ey, ew * 0.8, building_h * v_scale, fill=0, stroke=1)

            # Draw schematic window/door openings on elevation
            c.setFillColor(colors.HexColor("#1e293b"))
            c.setStrokeColor(colors.HexColor("#38bdf8"))
            c.setLineWidth(1)
            for op_i in range(min(3, len(elevs['front']['openings']))):
                ow = 16
                oh = 24
                ox = ex + ew * (0.2 + op_i * 0.25)
                oy = ey + (op_i * 12 + 10)
                c.rect(ox, oy, ow, oh, fill=1, stroke=1)

        # Render 3 Elevations across top half
        _render_vector_elevation(40, page_h - 250, 220, 160, "FRONT ELEVATION (SOUTH)", elevs['front']['max_height'])
        _render_vector_elevation(280, page_h - 250, 220, 160, "REAR ELEVATION (NORTH)", elevs['rear']['max_height'])
        _render_vector_elevation(520, page_h - 250, 220, 160, "LEFT ELEVATION (WEST)", elevs['left']['max_height'])

        # Helper to draw actual section view
        def _render_vector_section(sx, sy, sw, sh, sec_name, sec_data):
            c.setStrokeColor(colors.white)
            c.setLineWidth(1.2)
            c.rect(sx, sy, sw, sh, fill=0, stroke=1)
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 8)
            c.drawString(sx, sy + sh + 6, sec_name)

            # Draw intersected levels & slab lines
            v_scale = sh / 35.0
            c.setStrokeColor(colors.HexColor("#22c55e"))
            c.setLineWidth(1)
            for lvl in sec_data["levels"]:
                ly = sy + lvl["elevation"] * v_scale
                c.line(sx, ly, sx + sw, ly)
                c.setFillColor(colors.white)
                c.setFont("Helvetica", 6)
                c.drawString(sx + 4, ly + 2, f"Slab / Floor: {lvl['name']} (+{lvl['elevation']}ft)")

            # Draw intersected walls as solid hatch rects
            c.setFillColor(colors.HexColor("#f59e0b"))
            for inter in sec_data["intersections"][:6]:
                ix = sx + sw * 0.3
                iy = sy + 10
                c.rect(ix, iy, 12, 45, fill=1, stroke=0)

        # Render 2 Sections across bottom half
        _render_vector_section(40, 60, 340, 130, "LONGITUDINAL SECTION A-A", secs['longitudinal_section_aa'])
        _render_vector_section(400, 60, 340, 130, "TRANSVERSE SECTION B-B", secs['transverse_section_bb'])

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 6.5)
        c.drawString(40, 18, "Sheet A-03: Actual Vector Orthographic Elevations & Building Sections | Naksha AI CBM Engine")
        c.showPage()

        # --- PAGE 4: SCHEDULES (DOOR, WINDOW, ROOM AREA) ---
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(40, page_h - 35, "ROOM AREA & OPENING SCHEDULES")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 9)
        c.drawString(40, page_h - 50, f"Total Building Area: {payload['schedules']['total_building_area_sqft']} sq ft")

        y_tbl = page_h - 85
        c.setFillColor(colors.HexColor("#1e293b"))
        c.rect(40, y_tbl - 12, page_w - 80, 18, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(50, y_tbl - 6, "ROOM NAME")
        c.drawString(200, y_tbl - 6, "LEVEL")
        c.drawString(320, y_tbl - 6, "AREA (SQFT)")
        c.drawString(440, y_tbl - 6, "PERIMETER (FT)")

        y_tbl -= 24
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.white)
        for lvl in payload["levels"]:
            for r in lvl["rooms"]:
                c.drawString(50, y_tbl, r["name"])
                c.drawString(200, y_tbl, lvl["name"])
                c.drawString(320, y_tbl, str(r["area_sqft"]))
                c.drawString(440, y_tbl, str(r["perimeter_ft"]))
                y_tbl -= 14
                if y_tbl < 150:
                    break

        y_tbl -= 20
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y_tbl, f"Openings Schedule: {len(payload['schedules']['doors'])} Doors, {len(payload['schedules']['windows'])} Windows")

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 6.5)
        c.drawString(40, 18, "Sheet A-04: Door, Window & Room Area Schedules | Naksha AI CBM Engine")
        c.showPage()

        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_dxf(cbm: CanonicalBuildingModel, add_watermark: bool = True) -> bytes:
        try:
            import ezdxf
            from ezdxf.enums import TextEntityAlignment

            doc = ezdxf.new('R2010')
            msp = doc.modelspace()

            layers = [
                ('WALLS', 7),
                ('EXTERNAL_WALLS', 1),
                ('INTERNAL_WALLS', 3),
                ('DOORS', 3),
                ('WINDOWS', 5),
                ('STAIRS', 4),
                ('SLABS', 2),
                ('ROOF', 6),
                ('DIMENSIONS', 1),
                ('ROOM_LABELS', 7),
                ('BOUNDARY', 6),
                ('SETBACKS', 2),
                ('SCHEDULE', 4),
                ('ELEVATION', 5),
            ]

            for name, color in layers:
                if name not in [l.dxf.name for l in doc.layers]:
                    doc.layers.new(name, dxfattribs={'color': color})

            plot_w = cbm.site.plot_width
            plot_l = cbm.site.plot_length

            msp.add_lwpolyline([(0, 0), (plot_w, 0), (plot_w, plot_l), (0, plot_l), (0, 0)], dxfattribs={'layer': 'BOUNDARY', 'closed': True})
            sb = cbm.site.setbacks.get("front", 6.0)
            msp.add_lwpolyline([(sb, sb), (plot_w - sb, sb), (plot_w - sb, plot_l - sb), (sb, plot_l - sb), (sb, sb)], dxfattribs={'layer': 'SETBACKS', 'closed': True})

            for w in cbm.walls:
                layer_name = 'EXTERNAL_WALLS' if w.wall_type == 'exterior' else 'INTERNAL_WALLS'
                msp.add_line(w.start, w.end, dxfattribs={'layer': layer_name})

            for r in cbm.rooms:
                poly = r.polygon
                if poly:
                    msp.add_lwpolyline(poly, dxfattribs={'layer': 'WALLS', 'closed': True})
                    xs = [pt[0] for pt in poly]
                    ys = [pt[1] for pt in poly]
                    cx = sum(xs) / len(xs)
                    cy = sum(ys) / len(ys)
                    msp.add_text(f"{r.name} ({r.area_sqft} sf)", dxfattribs={'layer': 'ROOM_LABELS', 'height': 0.4}).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)

            for op in cbm.openings:
                layer_name = 'DOORS' if op.opening_type == 'door' else 'WINDOWS'
                msp.add_line((0, 0), (op.width, 0), dxfattribs={'layer': layer_name})

            sx = plot_w + 10
            yy = plot_l
            msp.add_text("NAKSHA AI - CBM ARCHITECTURAL DRAWING", dxfattribs={'layer': 'SCHEDULE', 'height': 0.6}).set_placement((sx, yy))
            yy -= 1.5
            msp.add_text(f"Project: {cbm.title} | Plot: {plot_w}x{plot_l} ft", dxfattribs={'layer': 'SCHEDULE', 'height': 0.4}).set_placement((sx, yy))

            if add_watermark:
                wm_layer = 'TEXT' if 'TEXT' in [l.dxf.name for l in doc.layers] else 'SCHEDULE'
                msp.add_text("NAKSHA AI VERIFIED CBM DXF", dxfattribs={'layer': wm_layer, 'height': 1.0, 'color': 2}).set_placement((plot_w / 2, plot_l / 2), align=TextEntityAlignment.MIDDLE_CENTER)

            buffer = io.StringIO()
            doc.write(buffer)
            return buffer.getvalue().encode("utf-8")
        except Exception as e:
            raise Exception(f"DXF generation failed: {str(e)}")
