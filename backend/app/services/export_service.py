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

        # Draw dark/blue-print architectural background
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        
        # Watermark for free users
        if add_watermark:
            c.saveState()
            c.setFillColor(colors.HexColor("#38bdf8"))
            c.setFont("Helvetica-Bold", 60)
            c.setFillAlpha(0.08)
            c.translate(page_w/2, page_h/2)
            c.rotate(45)
            c.drawCentredString(0, 0, "NAKSHAI - FREE VERSION")
            c.restoreState()

        # Blueprint grid
        c.setStrokeColor(colors.HexColor("#1e293b"))
        c.setLineWidth(0.5)
        for x in range(0, int(page_w), 20):
            c.line(x, 0, x, page_h)
        for y in range(0, int(page_h), 20):
            c.line(0, y, page_w, y)

        # Title Header
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, page_h - 40, f"NAKSHAI BLUEPRINT: {plan.title.upper()}")

        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        c.drawString(40, page_h - 58, f"Plot Dimensions: {plan.plot.width} ft x {plan.plot.length} ft | Total Area: {plan.plot.total_area_sqft} sq ft ({plan.plot.marla_size} Marla) | Project ID: {plan.id}")

        # Drawing area calculation
        draw_x = 40
        draw_y = 60
        max_draw_w = page_w - 260
        max_draw_h = page_h - 140

        scale = min(max_draw_w / max(1, plan.plot.width), max_draw_h / max(1, plan.plot.length))

        # Draw plot boundary
        c.setStrokeColor(colors.HexColor("#38bdf8"))
        c.setLineWidth(2)
        c.rect(draw_x, draw_y, plan.plot.width * scale, plan.plot.length * scale, fill=0, stroke=1)

        # Draw Rooms
        for room in plan.rooms:
            rx = draw_x + room.x * scale
            # Invert Y for PDF coordinate system
            ry = draw_y + (plan.plot.length - (room.y + room.length)) * scale
            rw = room.width * scale
            rl = room.length * scale

            # Room background & walls
            c.setFillColor(colors.HexColor("#1e293b"))
            c.setStrokeColor(colors.white)
            c.setLineWidth(1.5)
            c.rect(rx, ry, rw, rl, fill=1, stroke=1)

            # Room text
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 8)
            c.drawCentredString(rx + rw / 2, ry + rl / 2 + 4, room.name)
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.HexColor("#94a3b8"))
            c.drawCentredString(rx + rw / 2, ry + rl / 2 - 6, f"{int(room.width)}' x {int(room.length)}' ({int(room.width * room.length)} sqft)")
            if hasattr(room, 'floor_level') and room.floor_level and room.floor_level > 0:
                c.setFont("Helvetica-Bold", 6)
                c.setFillColor(colors.HexColor("#fbbf24"))
                c.drawCentredString(rx + rw / 2, ry + 10, f"FLOOR {room.floor_level}")

        # Draw Doors (simple indicators)
        c.setStrokeColor(colors.HexColor("#22c55e"))
        c.setLineWidth(2)
        for door in plan.doors[:20]:  # Limit to avoid clutter
            # Find room position
            for room in plan.rooms:
                if room.name == door.room_name:
                    rx = draw_x + room.x * scale
                    ry = draw_y + (plan.plot.length - (room.y + room.length)) * scale
                    # Simple door marker
                    if door.wall == "north":
                        c.line(rx + door.position * scale, ry, rx + (door.position + door.width) * scale, ry)
                    elif door.wall == "south":
                        c.line(rx + door.position * scale, ry + room.length * scale, rx + (door.position + door.width) * scale, ry + room.length * scale)
                    elif door.wall == "west":
                        c.line(rx, ry + door.position * scale, rx, ry + (door.position + door.width) * scale)
                    elif door.wall == "east":
                        c.line(rx + room.width * scale, ry + door.position * scale, rx + room.width * scale, ry + (door.position + door.width) * scale)
                    break

        # Right-side Material & Cost Panel
        panel_x = page_w - 200
        panel_y = page_h - 60

        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(panel_x, panel_y, "ESTIMATED MATERIALS")

        if plan.material_estimate:
            est = plan.material_estimate
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.white)
            items = [
                f"Covered Area: {est.covered_area_sqft} sq ft",
                f"Bricks: {est.bricks_count:,} pcs",
                f"Cement: {est.cement_bags:,} bags",
                f"Steel: {est.steel_tons} Tons",
                f"Sand: {est.sand_cft} cft",
                f"Crush: {est.crush_cft} cft",
                "",
                f"Estimated Cost:",
                f"PKR: Rs. {est.estimated_cost_pkr:,.0f}",
                f"USD: ${est.estimated_cost_usd:,.0f}"
            ]
            cur_y = panel_y - 20
            for item in items:
                if "PKR:" in item or "Estimated Cost:" in item:
                    c.setFont("Helvetica-Bold", 10)
                    c.setFillColor(colors.HexColor("#4ade80"))
                else:
                    c.setFont("Helvetica", 9)
                    c.setFillColor(colors.white)
                c.drawString(panel_x, cur_y, item)
                cur_y -= 16

        # Room Schedule
        c.showPage()
        c.setFillColor(colors.HexColor("#0f172a"))
        c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, page_h - 40, "NAKSHAI - ROOM SCHEDULE & BILL OF QUANTITIES")
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        c.drawString(40, page_h - 58, f"Project: {plan.title} | Plot: {plan.plot.width}' x {plan.plot.length}' ({plan.plot.marla_size} Marla)")

        # Room table
        c.setFillColor(colors.HexColor("#1e293b"))
        c.rect(40, page_h - 90, page_w - 80, 25, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#38bdf8"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, page_h - 74, "S.NO")
        c.drawString(90, page_h - 74, "ROOM NAME")
        c.drawString(250, page_h - 74, "TYPE")
        c.drawString(380, page_h - 74, "LENGTH (FT)")
        c.drawString(480, page_h - 74, "WIDTH (FT)")
        c.drawString(580, page_h - 74, "AREA (SQ.FT)")
        c.drawString(680, page_h - 74, "FLOOR")

        y = page_h - 115
        for idx, room in enumerate(plan.rooms):
            if room.type in ["lawn", "ots_duct"]:
                continue
            c.setFillColor(colors.HexColor("#0f172a") if idx % 2 == 0 else colors.HexColor("#1e293b"))
            c.rect(40, y - 15, page_w - 80, 20, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica", 8)
            c.drawString(50, y - 8, str(idx + 1))
            c.drawString(90, y - 8, room.name[:25])
            c.drawString(250, y - 8, room.type.replace("_", " ").upper()[:20])
            c.drawString(400, y - 8, f"{room.length}'")
            c.drawString(500, y - 8, f"{room.width}'")
            c.drawString(600, y - 8, f"{int(room.width * room.length)}")
            c.drawString(700, y - 8, f"F{getattr(room, 'floor_level', 0)}")
            y -= 20
            if y < 150:
                break

        # BOQ
        if plan.material_estimate:
            est = plan.material_estimate
            c.setFillColor(colors.HexColor("#1e293b"))
            c.rect(40, 120, page_w - 80, 25, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#4ade80"))
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, 137, "BILL OF QUANTITIES - GREY STRUCTURE")
            
            c.setFillColor(colors.white)
            c.setFont("Helvetica", 9)
            boq_items = [
                ["ITEM", "QUANTITY", "UNIT", "RATE (PKR)", "AMOUNT (PKR)"],
                ["Bricks (Awwal)", f"{est.bricks_count:,}", "Nos", "15", f"{est.bricks_count * 15:,.0f}"],
                ["Cement (OPC 50kg)", f"{est.cement_bags:,}", "Bags", "1350", f"{est.cement_bags * 1350:,.0f}"],
                ["Steel/Rebar (60 Grade)", f"{est.steel_tons}", "Tons", f"{260*1000:,.0f}", f"{est.steel_tons * 260000:,.0f}"],
                ["Sand (Ravi)", f"{est.sand_cft}", "Cft", "45", f"{est.sand_cft * 45:,.0f}"],
                ["Crush (Margalla)", f"{est.crush_cft}", "Cft", "115", f"{est.crush_cft * 115:,.0f}"],
            ]
            y_boq = 100
            for idx, row in enumerate(boq_items):
                if idx == 0:
                    c.setFillColor(colors.HexColor("#334155"))
                    c.setFont("Helvetica-Bold", 8)
                else:
                    c.setFillColor(colors.HexColor("#0f172a") if idx % 2 == 1 else colors.HexColor("#1e293b"))
                    c.setFont("Helvetica", 8)
                c.rect(40, y_boq - 12, page_w - 80, 18, fill=1, stroke=0)
                c.setFillColor(colors.white)
                c.drawString(50, y_boq - 5, row[0])
                c.drawString(200, y_boq - 5, row[1])
                c.drawString(300, y_boq - 5, row[2])
                c.drawString(380, y_boq - 5, row[3])
                c.drawString(500, y_boq - 5, row[4])
                y_boq -= 18
            
            c.setFillColor(colors.HexColor("#4ade80"))
            c.setFont("Helvetica-Bold", 10)
            c.drawString(380, y_boq - 5, "TOTAL ESTIMATED COST:")
            c.drawString(500, y_boq - 5, f"Rs. {est.estimated_cost_pkr:,.0f}")

        c.setFillColor(colors.HexColor("#64748b"))
        c.setFont("Helvetica", 7)
        c.drawString(40, 30, "Generated by NakshaAI - AI Powered Floor Plan & Building Map Generator | www.nakshai.app")
        c.drawString(page_w - 200, 30, f"Page 2 | Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}")

        if add_watermark:
            c.saveState()
            c.setFillColor(colors.HexColor("#f59e0b"))
            c.setFont("Helvetica-Bold", 12)
            c.setFillAlpha(0.3)
            c.drawString(page_w - 250, 15, "FREE VERSION - UPGRADE TO PRO FOR NO WATERMARK")
            c.restoreState()

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_dxf(plan: FloorPlan, add_watermark: bool = True) -> bytes:
        """Generate DXF CAD file for architects and draftsmen"""
        try:
            import ezdxf
            from ezdxf import zoom
            doc = ezdxf.new('R2010')
            msp = doc.modelspace()
            
            # Create layers
            doc.layers.new('WALLS', dxfattribs={'color': 7})
            doc.layers.new('DOORS', dxfattribs={'color': 3})
            doc.layers.new('WINDOWS', dxfattribs={'color': 5})
            doc.layers.new('ROOMS', dxfattribs={'color': 4})
            doc.layers.new('DIMENSIONS', dxfattribs={'color': 1})
            doc.layers.new('PLOT_BOUNDARY', dxfattribs={'color': 6})
            doc.layers.new('TEXT', dxfattribs={'color': 7})
            
            # Plot boundary
            w, l = plan.plot.width, plan.plot.length
            msp.add_lwpolyline([(0,0), (w,0), (w,l), (0,l), (0,0)], 
                              dxfattribs={'layer': 'PLOT_BOUNDARY', 'closed': True})
            
            # Draw rooms as walls
            for room in plan.rooms:
                if room.type in ["lawn", "ots_duct"]:
                    continue
                x, y = room.x, room.y
                rw, rl = room.width, room.length
                # Draw rectangle walls
                points = [(x,y), (x+rw,y), (x+rw,y+rl), (x,y+rl), (x,y)]
                msp.add_lwpolyline(points, dxfattribs={'layer': 'WALLS', 'closed': True})
                # Room label
                msp.add_text(f"{room.name} [{rw}x{rl}]", 
                           dxfattribs={'layer': 'TEXT', 'height': 0.5}).set_pos((x+rw/2-2, y+rl/2), align='MIDDLE_CENTER')
            
            # Doors
            for door in plan.doors:
                for room in plan.rooms:
                    if room.name == door.room_name:
                        x, y = room.x, room.y
                        if door.wall == "south":
                            msp.add_line((x+door.position, y), (x+door.position+door.width, y),
                                       dxfattribs={'layer': 'DOORS'})
                        elif door.wall == "north":
                            msp.add_line((x+door.position, y+room.length), (x+door.position+door.width, y+room.length),
                                       dxfattribs={'layer': 'DOORS'})
                        elif door.wall == "west":
                            msp.add_line((x, y+door.position), (x, y+door.position+door.width),
                                       dxfattribs={'layer': 'DOORS'})
                        elif door.wall == "east":
                            msp.add_line((x+room.width, y+door.position), (x+room.width, y+door.position+door.width),
                                       dxfattribs={'layer': 'DOORS'})
                        break
            
            # Windows
            for window in plan.windows:
                for room in plan.rooms:
                    if room.name == window.room_name:
                        x, y = room.x, room.y
                        if window.wall == "south":
                            msp.add_line((x+window.position, y), (x+window.position+window.width, y),
                                       dxfattribs={'layer': 'WINDOWS', 'linetype': 'DASHED'})
                        elif window.wall == "north":
                            msp.add_line((x+window.position, y+room.length), (x+window.position+window.width, y+room.length),
                                       dxfattribs={'layer': 'WINDOWS', 'linetype': 'DASHED'})
                        elif window.wall == "west":
                            msp.add_line((x, y+window.position), (x, y+window.position+window.width),
                                       dxfattribs={'layer': 'WINDOWS', 'linetype': 'DASHED'})
                        elif window.wall == "east":
                            msp.add_line((x+room.width, y+window.position), (x+room.width, y+window.position+window.width),
                                       dxfattribs={'layer': 'WINDOWS', 'linetype': 'DASHED'})
                        break
            
            # Title
            msp.add_text(f"NAKSHAI - {plan.title} - PLOT {w}'x{l}'", 
                       dxfattribs={'layer': 'TEXT', 'height': 0.8}).set_pos((w/2, l+5), align='MIDDLE_CENTER')
            if add_watermark:
                msp.add_text("NAKSHAI FREE VERSION - UPGRADE TO PRO", 
                           dxfattribs={'layer': 'TEXT', 'height': 0.4, 'color': 3}).set_pos((w/2, l+3), align='MIDDLE_CENTER')
            
            buffer = io.BytesIO()
            doc.saveas(buffer)
            buffer.seek(0)
            return buffer.getvalue()
        except Exception as e:
            raise Exception(f"DXF generation failed: {str(e)}")
