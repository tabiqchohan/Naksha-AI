import json
import re
import uuid
import logging
from typing import Dict, Any, List, Optional
from app.models.schemas import FloorPlan, Plot, Room, Door, Window, GeneratePlanRequest, FurnitureItem
from app.config import settings
from app.services.geometry_validator import GeometryValidator
from app.services.material_estimator import MaterialEstimator

logger = logging.getLogger(__name__)

PLOT_PRESETS = {
    "3_marla": {"width": 20.0, "length": 35.0, "marla": 3.0},
    "5_marla": {"width": 25.0, "length": 45.0, "marla": 5.0},
    "7_marla": {"width": 30.0, "length": 55.0, "marla": 7.0},
    "10_marla": {"width": 35.0, "length": 65.0, "marla": 10.0},
    "1_kanal": {"width": 50.0, "length": 90.0, "marla": 20.0},
    "mockup_50x60": {"width": 50.0, "length": 60.0, "marla": 13.3}
}

class AIEngine:
    ROOM_TYPE_ALIASES = {
        "master_bed": "master_bedroom", "master_bedroom": "master_bedroom", "master": "master_bedroom",
        "bed": "bedroom", "bed_room": "bedroom", "bedroom": "bedroom", "kids_room": "bedroom",
        "bath": "attached_bath", "bathroom": "attached_bath", "toilet": "attached_bath",
        "washroom": "attached_bath", "wc": "attached_bath", "powder": "powder_room", "powder_room": "powder_room",
        "kitchen": "kitchen", "dirty_kitchen": "dirty_kitchen", "service_kitchen": "dirty_kitchen",
        "living": "living_room", "living_room": "living_room", "lounge": "living_room",
        "hall": "living_room", "family_room": "living_room", "drawing": "drawing_room",
        "drawing_room": "drawing_room", "dining": "dining_room", "dining_room": "dining_room",
        "garage": "garage", "car_porch": "parking", "car_parking": "parking", "parking": "parking",
        "porch": "parking", "lawn": "lawn", "garden": "lawn", "courtyard": "lawn",
        "outdoor": "lawn", "open_area": "lawn", "ots": "ots_duct", "duct": "ots_duct",
        "ots_duct": "ots_duct", "balcony": "balcony", "stair": "staircase", "stairs": "staircase",
        "staircase": "staircase", "shop": "shop", "office": "office", "study": "office",
        "home_office": "office", "corridor": "corridor", "passage": "corridor", "hallway": "corridor",
        "ramp": "ramp", "lift": "lift_shaft", "elevator": "lift_shaft", "lift_shaft": "lift_shaft",
        "store": "store", "storage": "store", "store_room": "store", "prayer_room": "bedroom",
    }
    VALID_ROOM_TYPES = {
        "master_bedroom", "bedroom", "attached_bath", "powder_room", "kitchen", "dirty_kitchen",
        "living_room", "drawing_room", "dining_room", "garage", "lawn", "ots_duct", "balcony",
        "staircase", "shop", "office", "corridor", "parking", "ramp", "lift_shaft", "store",
    }
    WALL_ALIASES = {
        "n": "north", "north": "north", "s": "south", "south": "south",
        "e": "east", "east": "east", "w": "west", "west": "west",
        "top": "north", "bottom": "south", "left": "west", "right": "east",
    }

    @classmethod
    def _normalize_room_type(cls, raw_type: Any, name: Any = None) -> str:
        key = re.sub(r"[^a-z0-9]+", "_", str(raw_type or "").strip().lower()).strip("_")
        if key in cls.ROOM_TYPE_ALIASES:
            return cls.ROOM_TYPE_ALIASES[key]
        if key in cls.VALID_ROOM_TYPES:
            return key
        name_key = re.sub(r"[^a-z0-9]+", "_", str(name or "").strip().lower()).strip("_")
        name_checks = [
            ("powder", "powder_room"), ("bath", "attached_bath"), ("toilet", "attached_bath"),
            ("washroom", "attached_bath"), ("wc", "attached_bath"), ("kitchen", "kitchen"),
            ("dining", "dining_room"), ("drawing", "drawing_room"), ("living", "living_room"),
            ("lounge", "living_room"), ("hall", "living_room"), ("stair", "staircase"),
            ("lift", "lift_shaft"), ("elevator", "lift_shaft"), ("garage", "garage"),
            ("parking", "parking"), ("porch", "parking"), ("ramp", "ramp"), ("lawn", "lawn"),
            ("garden", "lawn"), ("courtyard", "lawn"), ("balcony", "balcony"), ("store", "store"),
            ("storage", "store"), ("duct", "ots_duct"), ("shop", "shop"), ("office", "office"),
            ("study", "office"), ("corridor", "corridor"), ("passage", "corridor"),
            ("master", "master_bedroom"), ("bed", "bedroom"),
        ]
        for token, mapped in name_checks:
            if token in name_key:
                return mapped
        return "living_room"

    @classmethod
    def _parse_ai_plan(cls, data: Any, plot: Plot) -> Optional[Dict[str, Any]]:
        if isinstance(data, str):
            text = data.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            try:
                data = json.loads(text)
            except Exception:
                return None
        if not isinstance(data, dict):
            return None

        rooms: List[Room] = []
        name_map: Dict[str, str] = {}
        for i, raw in enumerate(data.get("rooms") or []):
            if not isinstance(raw, dict):
                continue
            try:
                x = float(raw.get("x", 0))
                y = float(raw.get("y", 0))
                width = float(raw.get("width", 0))
                length = float(raw.get("length", 0))
            except (TypeError, ValueError):
                continue
            if width <= 0 or length <= 0:
                continue
            room_type = cls._normalize_room_type(raw.get("type"), raw.get("name"))
            name = str(raw.get("name") or room_type.replace("_", " ").title()).strip()
            if not name:
                name = room_type.replace("_", " ").title()
            room_data: Dict[str, Any] = {
                "id": str(raw.get("id") or f"r{i + 1}"),
                "name": name,
                "type": room_type,
                "x": max(0.0, x),
                "y": max(0.0, y),
                "width": width,
                "length": length,
            }
            color = str(raw.get("color") or "")
            if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
                room_data["color"] = color
            floor_level = raw.get("floor_level")
            if isinstance(floor_level, (int, float)):
                room_data["floor_level"] = int(floor_level)
            rooms.append(Room(**room_data))
            name_map[name.lower()] = name

        if not rooms:
            return None

        def parse_openings(items: Any, kind: str) -> List[Any]:
            parsed: List[Any] = []
            for j, raw in enumerate(items or []):
                if not isinstance(raw, dict):
                    continue
                room_name = str(raw.get("room_name") or raw.get("room") or "").strip()
                if room_name.lower() not in name_map:
                    continue
                wall = cls.WALL_ALIASES.get(str(raw.get("wall") or "").strip().lower())
                if not wall:
                    continue
                try:
                    position = float(raw.get("position", 0))
                    width = float(raw.get("width", 3.5 if kind == "door" else 4.0))
                except (TypeError, ValueError):
                    continue
                if width <= 0:
                    continue
                base = {
                    "id": str(raw.get("id") or f"{kind[0]}{j + 1}"),
                    "room_name": name_map[room_name.lower()],
                    "wall": wall,
                    "position": max(0.0, position),
                    "width": width,
                }
                parsed.append(Door(**base) if kind == "door" else Window(**base))
            return parsed

        return {
            "title": str(data.get("title") or f"AI Floor Plan ({plot.width}x{plot.length} ft)")[:200],
            "rooms": rooms,
            "doors": parse_openings(data.get("doors"), "door"),
            "windows": parse_openings(data.get("windows"), "window"),
        }

    @classmethod
    async def generate_floor_plan(cls, req: GeneratePlanRequest) -> FloorPlan:
        # Determine plot dimensions
        width = req.plot_width or 50.0
        length = req.plot_length or 60.0
        preset_marla = None
        building_type = req.building_type or "house"
        road_facing = req.road_facing or "east"
        floors = req.floors or 1

        if req.plot_preset and req.plot_preset in PLOT_PRESETS:
            preset = PLOT_PRESETS[req.plot_preset]
            width = preset["width"]
            length = preset["length"]
            preset_marla = preset["marla"]
        else:
            preset_marla = round((width * length) / 225.0, 1) # Standard 225 sqft/marla

        plot = Plot(
            width=width,
            length=length,
            unit="feet",
            marla_size=preset_marla,
            total_area_sqft=round(width * length, 1)
        )

        plan_data = None

        # 1. Try Gemini if configured and requested
        if (req.llm_provider in ["auto", "gemini"]) and settings.GEMINI_API_KEY:
            try:
                plan_data = await cls._generate_with_gemini(req, plot)
            except Exception as e:
                logger.error(f"Gemini API error: {e}. Falling back...")

        # 2. Try Groq if configured and not yet generated
        if not plan_data and (req.llm_provider in ["auto", "groq"]) and settings.GROQ_API_KEY:
            try:
                plan_data = await cls._generate_with_groq(req, plot)
            except Exception as e:
                logger.error(f"Groq API error: {e}. Falling back...")

        # 3. Use Smart Architectural Layout Generator
        if not plan_data:
            if building_type in ["plaza", "shop"]:
                plan_data = cls._generate_commercial_layout(req, plot)
            elif floors >= 2:
                plan_data = cls._generate_multistorey_layout(req, plot)
            else:
                plan_data = cls._generate_smart_architectural_layout(req, plot)

        # Post-process rooms, doors, windows & validate
        rooms, warnings = GeometryValidator.validate_and_correct_layout(plot, plan_data["rooms"], road_facing)
        rooms = GeometryValidator.auto_arrange_furniture(rooms)

        # Calculate material estimate
        material_est = MaterialEstimator.calculate_estimate(plot, rooms)

        plan = FloorPlan(
            id=str(uuid.uuid4())[:8],
            title=plan_data.get("title", f"NAKSHAI - {plot.width}x{plot.length} ft ({building_type.upper()})"),
            description=req.prompt or f"Custom {building_type} Layout - {req.bedrooms} Bed, {req.bathrooms} Bath, {floors} Floor(s)",
            plot=plot,
            rooms=rooms,
            doors=plan_data.get("doors", []),
            windows=plan_data.get("windows", []),
            material_estimate=material_est,
            warnings=warnings
        )
        return plan

    @classmethod
    def _generate_commercial_layout(cls, req: GeneratePlanRequest, plot: Plot) -> Dict[str, Any]:
        """Generate commercial plaza/shop layout with parking and frontage"""
        w = plot.width
        l = plot.length
        building_type = req.building_type or "plaza"

        rooms: List[Room] = []
        doors: List[Door] = []
        windows: List[Window] = []

        # Front parking/open area
        parking_w = w
        parking_l = round(l * 0.25, 1)
        rooms.append(Room(
            id="r_parking", name="PARKING AREA", type="parking",
            x=0.0, y=0.0, width=parking_w, length=parking_l, color="#94A3B8"
        ))

        # Shops along front
        shop_count = max(2, int(w / 12))
        shop_w = round(w / shop_count, 1)
        for i in range(shop_count):
            rooms.append(Room(
                id=f"r_shop{i+1}", name=f"SHOP {i+1}", type="shop",
                x=i * shop_w, y=parking_l,
                width=shop_w - 0.2, length=round(l * 0.35, 1),
                color="#F59E0B"
            ))
            doors.append(Door(id=f"d_shop{i+1}", room_name=f"SHOP {i+1}", wall="north", position=2.0, width=4.0))
            windows.append(Window(id=f"w_shop{i+1}", room_name=f"SHOP {i+1}", wall="north", position=6.0, width=3.0))

        # Corridor
        rooms.append(Room(
            id="r_corridor", name="CORRIDOR", type="corridor",
            x=0.0, y=parking_l + round(l * 0.35, 1),
            width=w, length=round(l * 0.12, 1), color="#64748B"
        ))

        # Offices/Units at back
        if building_type == "plaza":
            unit_w = round((w - 4) / 2, 1)
            unit_l = round(l * 0.28, 1)
            for i in range(2):
                rooms.append(Room(
                    id=f"r_unit{i+1}", name=f"OFFICE UNIT {i+1}", type="office",
                    x=2 + i * (unit_w + 0.5), y=parking_l + round(l * 0.35, 1) + round(l * 0.12, 1),
                    width=unit_w, length=unit_l, color="#3B82F6"
                ))
                doors.append(Door(id=f"d_unit{i+1}", room_name=f"OFFICE UNIT {i+1}", wall="north", position=unit_w/2, width=3.0))

        return {
            "title": f"NAKSHAI - Commercial {building_type.upper()} ({int(w)}x{int(l)} ft)",
            "rooms": rooms,
            "doors": doors,
            "windows": windows
        }

    @classmethod
    def _generate_multistorey_layout(cls, req: GeneratePlanRequest, plot: Plot) -> Dict[str, Any]:
        """Generate G+1 or multi-storey layout with staircase"""
        w = plot.width
        l = plot.length
        floors = req.floors or 2

        rooms: List[Room] = []
        doors: List[Door] = []
        windows: List[Window] = []

        # Left wing - Bedrooms
        left_w = round(w * 0.52, 1)
        right_w = round(w - left_w, 1)
        top_l = round(l * 0.54, 1)
        bottom_l = round(l - top_l, 1)

        # Ground floor
        rooms.append(Room(id="r_g_mbed1", name="GROUND MASTER BED", type="master_bedroom", x=0.0, y=0.0, width=left_w, length=top_l, color="#3B82F6", floor_level=0))
        doors.append(Door(id="d_g1", room_name="GROUND MASTER BED", wall="east", position=top_l - 4.0, width=3.5))
        windows.append(Window(id="w_g1", room_name="GROUND MASTER BED", wall="north", position=left_w * 0.35, width=4.5))

        rooms.append(Room(id="r_g_bed2", name="GROUND BED 2", type="bedroom", x=0.0, y=top_l, width=left_w, length=bottom_l, color="#60A5FA", floor_level=0))
        doors.append(Door(id="d_g2", room_name="GROUND BED 2", wall="east", position=2.0, width=3.5))

        # Staircase
        stair_w = 10.0
        stair_l = 12.0
        rooms.append(Room(id="r_stair", name="STAIRCASE", type="staircase", x=left_w + 2, y=0.0, width=stair_w, length=stair_l, color="#475569", floor_level=0))
        doors.append(Door(id="d_stair", room_name="STAIRCASE", wall="west", position=2.0, width=3.0))

        # Bath
        bath_w = 8.0
        rooms.append(Room(id="r_g_bath", name="BATH", type="attached_bath", x=left_w + stair_w + 4, y=0.0, width=bath_w, length=top_l * 0.5, color="#14B8A6", floor_level=0))
        doors.append(Door(id="d_g3", room_name="BATH", wall="south", position=1.0, width=2.5))

        # Kitchen & Living
        kitchen_w = right_w - stair_w - bath_w - 6
        rooms.append(Room(id="r_g_kitchen", name="KITCHEN", type="kitchen", x=left_w + stair_w + bath_w + 4, y=0.0, width=kitchen_w, length=top_l, color="#F59E0B", floor_level=0))
        doors.append(Door(id="d_g4", room_name="KITCHEN", wall="west", position=top_l - 4.0, width=3.5))

        rooms.append(Room(id="r_g_living", name="LIVING ROOM", type="living_room", x=left_w, y=top_l, width=right_w, length=bottom_l, color="#8B5CF6", floor_level=0))
        doors.append(Door(id="d_g5", room_name="LIVING ROOM", wall="south", position=right_w * 0.5, width=4.0))

        # First floor (duplicate layout with slight variation)
        if floors >= 2:
            rooms.append(Room(id="r_f1_mbed1", name="FIRST FLOOR MASTER BED", type="master_bedroom", x=0.0, y=0.0, width=left_w, length=top_l, color="#2563EB", floor_level=1))
            rooms.append(Room(id="r_f1_bed2", name="FIRST FLOOR BED 2", type="bedroom", x=0.0, y=top_l, width=left_w, length=bottom_l, color="#3B82F6", floor_level=1))
            rooms.append(Room(id="r_f1_bed3", name="FIRST FLOOR BED 3", type="bedroom", x=left_w + stair_w + 4, y=top_l, width=right_w - stair_w - 4, length=bottom_l, color="#60A5FA", floor_level=1))
            rooms.append(Room(id="r_f1_bath", name="FIRST FLOOR BATH", type="attached_bath", x=left_w + stair_w + 4, y=top_l, width=8.0, length=10.0, color="#0EA5E9", floor_level=1))
            doors.append(Door(id="d_f1_1", room_name="FIRST FLOOR BED 3", wall="west", position=2.0, width=3.0))

        return {
            "title": f"NAKSHAI - G+{floors-1} MULTI-STOREY ({int(w)}x{int(l)} ft)",
            "rooms": rooms,
            "doors": doors,
            "windows": windows
        }

    @classmethod
    def _generate_smart_architectural_layout(cls, req: GeneratePlanRequest, plot: Plot) -> Dict[str, Any]:
        """
        Creates a structurally sound, highly optimized architectural layout
        matching the ARCHI-GENIUS mockup image proportions (Master Beds on left,
        Kitchen & Living Room on right, Central Bath / Passage).
        """
        w = plot.width
        l = plot.length

        rooms: List[Room] = []
        doors: List[Door] = []
        windows: List[Window] = []

        # Proportions:
        # Left wing width: ~50-55% of plot
        # Right wing width: remaining plot width
        left_w = round(w * 0.52, 1)
        right_w = round(w - left_w, 1)

        # Top section length: ~55% of plot
        # Bottom section length: ~45% of plot
        top_l = round(l * 0.54, 1)
        bottom_l = round(l - top_l, 1)

        # 1. Master Bed 1 (Top Left)
        master1_w = left_w
        master1_l = top_l
        r_master1 = Room(
            id="r_master1",
            name="MASTER BED 1",
            type="master_bedroom",
            x=0.0,
            y=0.0,
            width=master1_w,
            length=master1_l,
            color="#3B82F6"
        )
        rooms.append(r_master1)
        doors.append(Door(id="d1", room_name="MASTER BED 1", wall="east", position=master1_l - 4.0, width=3.5))
        windows.append(Window(id="w1", room_name="MASTER BED 1", wall="north", position=master1_w * 0.35, width=4.5))

        # 2. Master Bed 2 (Bottom Left)
        master2_w = left_w
        master2_l = bottom_l
        r_master2 = Room(
            id="r_master2",
            name="MASTER BED 2",
            type="bedroom",
            x=0.0,
            y=top_l,
            width=master2_w,
            length=master2_l,
            color="#60A5FA"
        )
        rooms.append(r_master2)
        doors.append(Door(id="d2", room_name="MASTER BED 2", wall="east", position=2.0, width=3.5))
        windows.append(Window(id="w2", room_name="MASTER BED 2", wall="south", position=master2_w * 0.35, width=4.5))

        # 3. Bath (Center/Top-Middle between Master Bed & Kitchen)
        bath_w = round(right_w * 0.40, 1)
        bath_l = round(top_l * 0.55, 1)
        r_bath = Room(
            id="r_bath1",
            name="BATH",
            type="attached_bath",
            x=left_w,
            y=0.0,
            width=bath_w,
            length=bath_l,
            color="#14B8A6"
        )
        rooms.append(r_bath)
        doors.append(Door(id="d3", room_name="BATH", wall="south", position=1.0, width=2.5))
        windows.append(Window(id="w3", room_name="BATH", wall="north", position=1.0, width=2.5))

        # 4. Kitchen (Top Right)
        kitchen_w = round(right_w - bath_w, 1)
        kitchen_l = top_l
        r_kitchen = Room(
            id="r_kitchen",
            name="KITCHEN",
            type="kitchen",
            x=round(left_w + bath_w, 1),
            y=0.0,
            width=kitchen_w,
            length=kitchen_l,
            color="#F59E0B"
        )
        rooms.append(r_kitchen)
        doors.append(Door(id="d4", room_name="KITCHEN", wall="west", position=kitchen_l - 4.0, width=3.5))
        windows.append(Window(id="w4", room_name="KITCHEN", wall="east", position=kitchen_l * 0.35, width=4.0))

        # 5. Living Room / Hall (Bottom Right)
        living_w = right_w
        living_l = bottom_l
        r_living = Room(
            id="r_living",
            name="LIVING ROOM",
            type="living_room",
            x=left_w,
            y=top_l,
            width=living_w,
            length=living_l,
            color="#8B5CF6"
        )
        rooms.append(r_living)
        doors.append(Door(id="d5", room_name="LIVING ROOM", wall="south", position=living_w * 0.5, width=4.0))
        windows.append(Window(id="w5", room_name="LIVING ROOM", wall="east", position=living_l * 0.4, width=5.0))

        return {
            "title": f"Modern Home Layout ({int(w)}x{int(l)} ft)",
            "rooms": rooms,
            "doors": doors,
            "windows": windows
        }

    @classmethod
    async def _generate_with_gemini(cls, req: GeneratePlanRequest, plot: Plot) -> Optional[Dict[str, Any]]:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json"}
        )

        prompt = f"""
        Act as an expert architectural designer. Generate a 2D floor plan layout coordinates for a plot of width {plot.width} ft and length {plot.length} ft.
        User requirement: "{req.prompt}". Bedrooms: {req.bedrooms}, Bathrooms: {req.bathrooms}, Style: {req.style}.

        Strict rules:
        1. All rooms must fit inside plot (0,0) to ({plot.width}, {plot.length}).
        2. No room may overlap with another.
        3. Wall coordinates (x, y, width, length) must be in feet.
        4. Include doors (room_name, wall, position, width) and windows (room_name, wall, position, width).
        5. Return strict JSON matching this structure:
        {{
          "title": "Project Title",
          "rooms": [
             {{"id": "r1", "name": "MASTER BED", "type": "master_bedroom", "x": 0, "y": 0, "width": 18, "length": 20}},
             {{"id": "r2", "name": "BATH", "type": "attached_bath", "x": 18, "y": 0, "width": 8, "length": 10}},
             {{"id": "r3", "name": "KITCHEN", "type": "kitchen", "x": 26, "y": 0, "width": 14, "length": 18}},
             {{"id": "r4", "name": "LIVING ROOM", "type": "living_room", "x": 18, "y": 18, "width": 22, "length": 22}}
          ],
          "doors": [{{"id": "d1", "room_name": "MASTER BED", "wall": "south", "position": 2, "width": 3.5}}],
          "windows": [{{"id": "w1", "room_name": "MASTER BED", "wall": "north", "position": 4, "width": 4.0}}]
        }}
        """

        response = await model.generate_content_async(prompt)
        parsed = cls._parse_ai_plan(response.text, plot)
        if not parsed:
            raise ValueError("Gemini returned no usable rooms")
        return parsed

    @classmethod
    async def _generate_with_groq(cls, req: GeneratePlanRequest, plot: Plot) -> Optional[Dict[str, Any]]:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        system_prompt = "You are an expert architectural engine that outputs strictly valid JSON floor plan coordinate geometry without overlapping rooms."
        user_prompt = f"""
        Generate floor plan JSON for plot width {plot.width} ft and length {plot.length} ft.
        Requirements: {req.prompt}. Bedrooms: {req.bedrooms}, Bathrooms: {req.bathrooms}.
        Return format:
        {{
          "title": "Title",
          "rooms": [{{"id": "r1", "name": "Master Bed", "type": "master_bedroom", "x": 0, "y": 0, "width": 18, "length": 20}}],
          "doors": [{{"id": "d1", "room_name": "Master Bed", "wall": "south", "position": 2, "width": 3.5}}],
          "windows": [{{"id": "w1", "room_name": "Master Bed", "wall": "north", "position": 4, "width": 4.0}}]
        }}
        """

        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_MODEL,
            response_format={"type": "json_object"}
        )

        content = chat_completion.choices[0].message.content
        parsed = cls._parse_ai_plan(content, plot)
        if not parsed:
            raise ValueError("Groq returned no usable rooms")
        return parsed
