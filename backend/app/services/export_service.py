import io
from app.models.schemas import FloorPlan

class ExportService:
    @staticmethod
    def generate_blueprint_pdf(plan: FloorPlan, add_watermark: bool = True) -> bytes:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(letter))
        page_w, page_h = landscape(letter)

        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        if add_watermark:
            c.saveState()
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 60)
            c.setFillAlpha(0.08)
            c.translate(page_w/2, page_h/2)
            c.rotate(45)
            c.drawCentredString(0, 0, "NAKSHAI - FREE VERSION")
            c.restoreState()

        c.setStrokeColor(colors.HexColor("#1e293b"))
        c.setLineWidth(0.5)
        for x in range(0, int(page_w), 20): c.line(x, 0, x, page_h)
        for y in range(0, int(page_h), 20): c.line(0, y, page_w, y)

        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, page_h - 40, f"NAKSHAI BLUEPRINT: {plan.title.upper()}")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        c.drawString(40, page_h - 58, f"Plot: {plan.plot.width} ft x {plan.plot.length} ft | {plan.plot.total_area_sqft} sq ft ({plan.plot.marla_size} Marla) | ID: {plan.id}")
        bylaws = plan.bylaws_report or {}
        if bylaws:
            c.setFillColor(colors.HexColor("#4ade80") if bylaws.get('passed') else colors.HexColor("#fbbf24"))
            c.drawString(40, page_h - 72, f"Bylaws ({bylaws.get('pack_name','Concept')}): {'PASS' if bylaws.get('passed') else 'REVIEW'}")

        draw_x, draw_y = 40, 60
        max_draw_w, max_draw_h = page_w - 260, page_h - 150
        scale = min(max_draw_w / max(1, plan.plot.width), max_draw_h / max(1, plan.plot.length))
        c.setStrokeColor(colors.HexColor("#38bdf8"))
        c.setLineWidth(2)
        c.rect(draw_x, draw_y, plan.plot.width * scale, plan.plot.length * scale, fill=0, stroke=1)
        for room in plan.rooms:
            rx = draw_x + room.x * scale
            ry = draw_y + (plan.plot.length - (room.y + room.length)) * scale
            rw, rl = room.width * scale, room.length * scale
            c.setFillColor(colors.HexColor("#1e293b"))
            c.setStrokeColor(colors.white)
            c.setLineWidth(1.2)
            c.rect(rx, ry, rw, rl, fill=1, stroke=1)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(rx + rw / 2, ry + rl / 2 + 3, (room.name or '')[:18])
            c.setFont("Helvetica", 6)
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.drawCentredString(rx + rw / 2, ry + rl / 2 - 5, f"{int(room.width)}'x{int(room.length)}' ({int(room.width*room.length)}sf)")
        c.setStrokeColor(colors.HexColor("#22c55e"))
        c.setLineWidth(2)
        for door in plan.doors[:25]:
            for room in plan.rooms:
                if room.name == door.room_name:
                    rx = draw_x + room.x * scale
                    ry = draw_y + (plan.plot.length - (room.y + room.length)) * scale
                    if door.wall == "north": c.line(rx + door.position*scale, ry, rx + (door.position+door.width)*scale, ry)
                    elif door.wall == "south": c.line(rx + door.position*scale, ry + room.length*scale, rx + (door.position+door.width)*scale, ry + room.length*scale)
                    elif door.wall == "west": c.line(rx, ry + door.position*scale, rx, ry + (door.position+door.width)*scale)
                    elif door.wall == "east": c.line(rx + room.width*scale, ry + door.position*scale, rx + room.width*scale, ry + (door.position+door.width)*scale)
                    break
        panel_x = page_w - 200
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 11)
        c.drawString(panel_x, page_h - 90, "SUMMARY")
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.white)
        lines = [f"Covered: {(plan.material_estimate.covered_area_sqft if plan.material_estimate else 0)} sf", f"Rooms: {len(plan.rooms)}"]
        if plan.material_estimate:
            lines += [f"Bricks: {plan.material_estimate.bricks_count:,}", f"Cement: {plan.material_estimate.cement_bags:,}", f"Steel: {plan.material_estimate.steel_tons}T", f"Cost: Rs.{plan.material_estimate.estimated_cost_pkr:,.0f}"]
        if bylaws:
            lines += ["", f"Bylaws: {'PASS' if bylaws.get('passed') else 'REVIEW'}"]
        y = page_h - 106
        for ln in lines:
            c.drawString(panel_x, y, ln); y -= 12
        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 6.5)
        c.drawString(40, 18, "AI-generated concept. Verify dimensions/bylaws with licensed architect/engineer and local authority before construction.")
        c.showPage()

        c.setFillColor(colors.HexColor("#0f172a")); c.rect(0,0,page_w,page_h,fill=1,stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8")); c.setFont("Helvetica-Bold", 14)
        c.drawString(40, page_h - 35, "ROOM SCHEDULE / BOQ / COMPLIANCE (CONCEPT)")
        c.setFillColor(colors.white); c.setFont("Helvetica", 8)
        c.drawString(40, page_h - 50, f"{plan.title} | {plan.plot.width}'x{plan.plot.length}'")
        y = page_h - 72
        c.setFillColor(colors.HexColor("#1e293b")); c.rect(40, y-10, page_w-80, 16, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8")); c.setFont("Helvetica-Bold", 7)
        for x,t in [(45,'ROOM'),(220,'TYPE'),(360,'SIZE'),(460,'AREA'),(540,'FLOOR')]: c.drawString(x, y-5, t)
        y -= 22; c.setFont("Helvetica", 7); c.setFillColor(colors.white)
        for i,r in enumerate([r for r in plan.rooms if r.type not in ['lawn','ots_duct']][:18]):
            c.drawString(45,y,f"{r.name[:28]}"); c.drawString(220,y,r.type[:18]); c.drawString(360,y,f"{int(r.width)}x{int(r.length)}"); c.drawString(460,y,f"{int(r.width*r.length)}"); c.drawString(540,y,f"F{getattr(r,'floor_level',0)}"); y-=13
        if plan.material_estimate:
            est = plan.material_estimate; y -= 8
            c.setFillColor(colors.HexColor("#4ade80")); c.setFont("Helvetica-Bold", 9); c.drawString(40,y,"BILL OF QUANTITIES (GREY STRUCTURE, ESTIMATE)"); y-=14
            c.setFillColor(colors.white); c.setFont("Helvetica", 7)
            for row in [["Bricks",f"{est.bricks_count:,} nos"],["Cement",f"{est.cement_bags:,} bags"],["Steel",f"{est.steel_tons} tons"],["Sand",f"{est.sand_cft} cft"],["Crush",f"{est.crush_cft} cft"],["Estimated Cost",f"Rs. {est.estimated_cost_pkr:,.0f} / ${est.estimated_cost_usd:,.0f}"]]:
                c.drawString(45,y,f"{row[0]}: {row[1]}"); y-=12
        if bylaws and bylaws.get('checks'):
            y -= 6; c.setFillColor(colors.HexColor("#fbbf24")); c.setFont("Helvetica-Bold", 9); c.drawString(40,max(40,y),"BYLAWS CHECK (CONCEPT)"); y-=13
            c.setFillColor(colors.white); c.setFont("Helvetica", 6.5)
            for chk in (bylaws.get('checks') or [])[:8]:
                c.drawString(45,max(30,y),f"[{str(chk.get('status','')).upper()}] {chk.get('title')}: {chk.get('actual','')} (req {chk.get('required','')})"); y-=10
        vastu = plan.vastu_report or {}
        if vastu:
            c.setFillColor(colors.HexColor("#a78bfa")); c.setFont("Helvetica-Bold", 8); c.drawString(430, page_h-90, f"VASTU ADVISORY: {vastu.get('score','-')}/100")
            c.setFillColor(colors.white); c.setFont("Helvetica", 6.5); yy = page_h-103
            for it in (vastu.get('items') or [])[:6]:
                c.drawString(430,max(30,yy),f"- {it.get('room')}: {it.get('status')}"); yy-=9
        # Door / window schedule (concept)
        c.setFillColor(colors.HexColor("#38bdf8")); c.setFont("Helvetica-Bold", 8); c.drawString(430, page_h-178, "DOOR / WINDOW SCHEDULE (CONCEPT)")
        c.setFillColor(colors.white); c.setFont("Helvetica", 6.2); dwy = page_h-191
        for d in (plan.doors or [])[:5]:
            c.drawString(430, dwy, f"D-{str(d.id)[:4]} {str(d.room_name)[:14]} {d.width}ft {d.wall}"); dwy-=8
        for w in (plan.windows or [])[:5]:
            c.drawString(430, dwy, f"W-{str(w.id)[:4]} {str(w.room_name)[:14]} {w.width}ft {w.wall}"); dwy-=8
        impact = plan.impact_summary or {}
        if impact:
            c.setFillColor(colors.HexColor("#38bdf8")); c.setFont("Helvetica-Bold", 8); c.drawString(430, 210, "SUN/VENT + STRUCTURAL/MEP (CONCEPT)")
            c.setFillColor(colors.white); c.setFont("Helvetica", 6.2); yy=197
            sv = impact.get('sun_ventilation') or {}; sc = impact.get('structural_concept') or {}; mep = impact.get('mep_concept') or {}
            for ln in [f"Sun: {sv.get('morning_east','')[:48]}", f"Vent: {sv.get('cross_ventilation','')[:48]}", f"Structure: {sc.get('system','')[:48]}", f"MEP: {(mep.get('electrical','')[:48])}"]:
                c.drawString(430,max(30,yy),ln); yy-=9
        c.setFillColor(colors.HexColor("#64748b")); c.setFont("Helvetica", 6)
        c.drawString(40, 18, "Disclaimer: AI concept only. Not a legal/structural/submission drawing. Verify all bylaws, structure, MEP, sun/ventilation, and costs with licensed professionals.")
        c.showPage()

        # Page 3: concept elevations & section
        c.setFillColor(colors.HexColor("#0f172a")); c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8")); c.setFont("Helvetica-Bold", 14)
        c.drawString(40, page_h - 35, "ELEVATIONS & SECTION (CONCEPT)")
        c.setFillColor(colors.white); c.setFont("Helvetica", 8)
        c.drawString(40, page_h - 50, f"{plan.title} | {plan.plot.width}'x{plan.plot.length}' | Concept massing only — not construction documents")
        floors = max(1, max([getattr(r, 'floor_level', 0) or 0 for r in plan.rooms] or [0]) + 1)
        wall_h = 10.0
        total_h = floors * wall_h
        gray = colors.HexColor("#475569"); blue = colors.HexColor("#38bdf8")

        def _elevation(x, y, w, h, label, openings):
            c.setStrokeColor(colors.white); c.setLineWidth(1.1); c.rect(x, y, w, h, fill=0, stroke=1)
            c.setStrokeColor(gray); c.setLineWidth(0.5)
            for f in range(1, floors):
                c.line(x, y + (h / floors) * f, x + w, y + (h / floors) * f)
            c.setFillColor(blue)
            n = max(1, openings)
            ow = max(3, (w / (n * 2 + 1)))
            for i in range(n):
                ox = x + ow * (i * 2 + 1)
                c.rect(ox, y + (h / floors) * 0.25, ow, (h / floors) * 0.45, fill=1, stroke=0)
            c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 7.5)
            c.drawCentredString(x + w / 2, y - 12, label)

        front_openings = len([w for w in (plan.windows or []) if w.wall in ['north', 'south']]) or 2
        side_openings = len([w for w in (plan.windows or []) if w.wall in ['east', 'west']]) or 2
        _elevation(50, page_h - 250, 280, total_h * 13, "FRONT ELEVATION (CONCEPT)", front_openings)
        _elevation(400, page_h - 250, 300, total_h * 13, "SIDE ELEVATION (CONCEPT)", side_openings)

        # Section (concept)
        sx, sy, sw, sh = 50, 100, 650, 110
        c.setStrokeColor(colors.white); c.setLineWidth(1.1); c.rect(sx, sy, sw, sh, fill=0, stroke=1)
        c.setStrokeColor(gray); c.setLineWidth(0.6)
        for f in range(1, floors):
            c.line(sx, sy + (sh / floors) * f, sx + sw, sy + (sh / floors) * f)
        c.setStrokeColor(colors.HexColor("#22c55e"))
        c.line(sx, sy, sx, sy + sh)
        c.setStrokeColor(colors.HexColor("#f59e0b"))
        c.line(40, sy, page_w - 40, sy)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(sx + sw / 2, sy - 12, "SECTION A-A (CONCEPT)")
        c.setFont("Helvetica", 6.5); c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawString(sx, sy + sh + 6, f"{floors} storey concept | assume {int(wall_h)} ft floor-to-floor | slab/beam/foundation sizes require structural engineer")
        c.setFillColor(colors.HexColor("#64748b")); c.setFont("Helvetica", 6)
        c.drawString(40, 18, "Disclaimer: Concept elevations/section only. Not architectural/structural submission drawings. Verify all dimensions, bylaws, structure, and MEP with licensed professionals.")
        c.showPage(); c.save(); buffer.seek(0); return buffer.getvalue()

    @staticmethod
    def generate_dxf(plan: FloorPlan, add_watermark: bool = True) -> bytes:
        try:
            import ezdxf
            from ezdxf.enums import TextEntityAlignment
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            for name, color in [('WALLS',7),('DOORS',3),('WINDOWS',5),('ROOMS',4),('DIMENSIONS',1),('PLOT_BOUNDARY',6),('TEXT',7),('SETBACKS',2),('SCHEDULE',4),('ELEVATION',5)]:
                if name not in [l.dxf.name for l in doc.layers]: doc.layers.new(name, dxfattribs={'color': color})
            w,l = plan.plot.width, plan.plot.length
            msp.add_lwpolyline([(0,0),(w,0),(w,l),(0,l),(0,0)], dxfattribs={'layer':'PLOT_BOUNDARY','closed':True})
            sb = 5
            msp.add_lwpolyline([(sb,sb),(w-sb,sb),(w-sb,l-sb),(sb,l-sb),(sb,sb)], dxfattribs={'layer':'SETBACKS','closed':True})
            for room in plan.rooms:
                if room.type in ['lawn','ots_duct']: continue
                x,y,rw,rl = room.x,room.y,room.width,room.length
                msp.add_lwpolyline([(x,y),(x+rw,y),(x+rw,y+rl),(x,y+rl),(x,y)], dxfattribs={'layer':'WALLS','closed':True})
                msp.add_text(f"{room.name} {rw}x{rl}", dxfattribs={'layer':'TEXT','height':0.45}).set_placement((x+rw/2,y+rl/2), align=TextEntityAlignment.MIDDLE_CENTER)
            for door in (plan.doors or []):
                for room in plan.rooms:
                    if room.name == door.room_name:
                        x,y=room.x,room.y
                        if door.wall=='south': msp.add_line((x+door.position,y),(x+door.position+door.width,y), dxfattribs={'layer':'DOORS'})
                        elif door.wall=='north': msp.add_line((x+door.position,y+room.length),(x+door.position+door.width,y+room.length), dxfattribs={'layer':'DOORS'})
                        elif door.wall=='west': msp.add_line((x,y+door.position),(x,y+door.position+door.width), dxfattribs={'layer':'DOORS'})
                        elif door.wall=='east': msp.add_line((x+room.width,y+door.position),(x+room.width,y+door.position+door.width), dxfattribs={'layer':'DOORS'})
                        break
            for window in (plan.windows or []):
                for room in plan.rooms:
                    if room.name == window.room_name:
                        x,y=room.x,room.y
                        if window.wall=='south': msp.add_line((x+window.position,y),(x+window.position+window.width,y), dxfattribs={'layer':'WINDOWS'})
                        elif window.wall=='north': msp.add_line((x+window.position,y+room.length),(x+window.position+window.width,y+room.length), dxfattribs={'layer':'WINDOWS'})
                        elif window.wall=='west': msp.add_line((x,y+window.position),(x,y+window.position+window.width), dxfattribs={'layer':'WINDOWS'})
                        elif window.wall=='east': msp.add_line((x+room.width,y+window.position),(x+room.width,y+window.position+window.width), dxfattribs={'layer':'WINDOWS'})
                        break
            # Concept door/window schedule + elevation beside the plan
            sx = w + 12
            yy = l
            msp.add_text("DOOR / WINDOW SCHEDULE (CONCEPT)", dxfattribs={'layer':'SCHEDULE','height':0.6}).set_placement((sx, yy))
            yy -= 2
            for door in (plan.doors or [])[:12]:
                msp.add_text(f"D {door.id} {door.room_name[:18]} {door.width}ft {door.wall}", dxfattribs={'layer':'SCHEDULE','height':0.35}).set_placement((sx, yy)); yy -= 1.1
            for window in (plan.windows or [])[:12]:
                msp.add_text(f"W {window.id} {window.room_name[:18]} {window.width}ft {window.wall}", dxfattribs={'layer':'SCHEDULE','height':0.35}).set_placement((sx, yy)); yy -= 1.1
            floors = max(1, max([getattr(r, 'floor_level', 0) or 0 for r in plan.rooms] or [0]) + 1)
            eh = floors * 10.0
            msp.add_lwpolyline([(sx, 0), (sx + w, 0), (sx + w, eh), (sx, eh), (sx, 0)], dxfattribs={'layer':'ELEVATION','closed':True})
            for f in range(1, floors):
                msp.add_line((sx, f * 10.0), (sx + w, f * 10.0), dxfattribs={'layer':'ELEVATION'})
            msp.add_text(f"FRONT ELEVATION (CONCEPT) {floors} STOREY", dxfattribs={'layer':'ELEVATION','height':0.45}).set_placement((sx + w/2, eh + 1.5), align=TextEntityAlignment.MIDDLE_CENTER)
            msp.add_text(f"NAKSHAI {plan.title} {w}x{l}FT", dxfattribs={'layer':'TEXT','height':0.7}).set_placement((w/2,l+4), align=TextEntityAlignment.MIDDLE_CENTER)
            msp.add_text("CONCEPT ONLY - VERIFY BYLAWS/STRUCTURE WITH LICENSED PROFESSIONALS", dxfattribs={'layer':'TEXT','height':0.35,'color':3}).set_placement((w/2,l+2.5), align=TextEntityAlignment.MIDDLE_CENTER)
            if add_watermark: msp.add_text("NAKSHAI FREE", dxfattribs={'layer':'TEXT','height':1.2,'color':2}).set_placement((w/2,l/2), align=TextEntityAlignment.MIDDLE_CENTER)
            buffer = io.StringIO(); doc.write(buffer); return buffer.getvalue().encode("utf-8")
        except Exception as e:
            raise Exception(f"DXF generation failed: {str(e)}")
