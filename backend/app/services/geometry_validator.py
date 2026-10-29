from typing import List, Tuple, Dict, Any
from app.models.schemas import Room, Plot, Door, Window

class GeometryValidator:
    @staticmethod
    def calculate_setbacks(plot: Plot, road_facing: str = "east") -> Dict[str, float]:
        """Calculate building setbacks as per Pakistani building bylaws (typical)"""
        w = plot.width
        l = plot.length
        area = w * l
        
        # Setback rules (approximate - can be customized)
        if area >= 4500:  # 1 Kanal+
            front = 10.0
            rear = 10.0
            side1 = 5.0
            side2 = 5.0
        elif area >= 2250:  # 10 Marla
            front = 8.0
            rear = 8.0
            side1 = 5.0
            side2 = 5.0
        elif area >= 1575:  # 7 Marla
            front = 7.0
            rear = 7.0
            side1 = 4.0
            side2 = 4.0
        elif area >= 1125:  # 5 Marla
            front = 6.0
            rear = 6.0
            side1 = 3.0
            side2 = 3.0
        else:  # 3 Marla and smaller
            front = 5.0
            rear = 5.0
            side1 = 3.0
            side2 = 3.0
        
        # Adjust based on road facing
        setbacks = {
            "front": front,
            "rear": rear,
            "left": side1,
            "right": side2,
            "road_facing": road_facing
        }
        setbacks["buildable_x"] = side1
        setbacks["buildable_y"] = front  # assuming front is along y=0 from road
        setbacks["buildable_width"] = w - side1 - side2
        setbacks["buildable_length"] = l - front - rear
        return setbacks
    
    @staticmethod
    def validate_and_correct_layout(plot: Plot, rooms: List[Room], road_facing: str = "east") -> Tuple[List[Room], List[str]]:
        warnings = []
        plot_w = plot.width
        plot_l = plot.length
        
        setbacks = GeometryValidator.calculate_setbacks(plot, road_facing)
        buildable_x = setbacks["buildable_x"]
        buildable_y = setbacks["buildable_y"]
        buildable_w = setbacks["buildable_width"]
        buildable_l = setbacks["buildable_length"]
        
        warnings.append(f"Setbacks applied: Front {setbacks['front']}ft, Sides {setbacks['left']}/{setbacks['right']}ft, Rear {setbacks['rear']}ft. Buildable area: {int(buildable_w)}' x {int(buildable_l)}'")

        # 1. Calculate sqft for each room
        for r in rooms:
            r.sqft = round(r.width * r.length, 1)

        # 2. Check Boundary violations (respect setbacks for covered rooms)
        for r in rooms:
            # Skip open areas from setback check
            if r.type in ["lawn", "ots_duct"]:
                if r.x < 0 or r.y < 0:
                    r.x = max(0.0, r.x)
                    r.y = max(0.0, r.y)
                continue
                
            # Check if room is outside buildable area
            if r.x < buildable_x:
                warnings.append(f"Room '{r.name}' violates front/side setback. Adjusting to buildable zone.")
                r.x = buildable_x
            if r.y < buildable_y:
                warnings.append(f"Room '{r.name}' violates front setback. Adjusting to buildable zone.")
                r.y = buildable_y
            if r.x < 0 or r.y < 0:
                warnings.append(f"Room '{r.name}' starts outside the plot boundary.")
                r.x = max(buildable_x, r.x)
                r.y = max(buildable_y, r.y)

            if (r.x + r.width) > plot_w - setbacks["right"]:
                warnings.append(f"Room '{r.name}' violates side/rear setback ({plot_w}ft).")
                if r.width <= buildable_w:
                    r.x = max(buildable_x, plot_w - setbacks["right"] - r.width)

            if (r.y + r.length) > plot_l - setbacks["rear"]:
                warnings.append(f"Room '{r.name}' violates rear setback ({plot_l}ft).")
                if r.length <= buildable_l:
                    r.y = max(buildable_y, plot_l - setbacks["rear"] - r.length)

        # 3. Check Overlaps
        n = len(rooms)
        for i in range(n):
            for j in range(i + 1, n):
                r1 = rooms[i]
                r2 = rooms[j]
                if r1.type in ["lawn", "ots_duct"] or r2.type in ["lawn", "ots_duct"]:
                    continue

                # Check AABB collision (allow touching edges)
                overlap_x = max(0.0, min(r1.x + r1.width, r2.x + r2.width) - max(r1.x, r2.x))
                overlap_y = max(0.0, min(r1.y + r1.length, r2.y + r2.length) - max(r1.y, r2.y))

                if overlap_x > 0.5 and overlap_y > 0.5:
                    warnings.append(f"Rooms '{r1.name}' and '{r2.name}' overlap by {round(overlap_x * overlap_y, 1)} sq ft.")

        return rooms, warnings

    @staticmethod
    def auto_arrange_furniture(rooms: List[Room]) -> List[Room]:
        """Adds architectural standard furniture to rooms if not already populated."""
        from app.models.schemas import FurnitureItem
        import uuid

        for r in rooms:
            if r.furniture and len(r.furniture) > 0:
                continue

            r_type = r.type
            w = r.width
            l = r.length

            if r_type in ["master_bedroom", "bedroom"]:
                # Place King/Queen bed along top or left wall
                bed_w = min(6.5, w * 0.5)
                bed_l = min(7.0, l * 0.55)
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="double_bed",
                    x=round((w - bed_w) / 2, 2),
                    y=round(1.0, 2),
                    width=bed_w,
                    length=bed_l,
                    rotation=0
                ))
            elif r_type in ["living_room", "drawing_room"]:
                # L-sofa & TV unit
                sofa_w = min(8.0, w * 0.6)
                sofa_l = min(6.0, l * 0.5)
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="l_sofa",
                    x=round(1.5, 2),
                    y=round(1.5, 2),
                    width=sofa_w,
                    length=sofa_l,
                    rotation=0
                ))
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="tv_unit",
                    x=round(w - 2.0, 2),
                    y=round(l / 2 - 2.0, 2),
                    width=1.5,
                    length=4.0,
                    rotation=90
                ))
            elif r_type in ["kitchen", "dirty_kitchen"]:
                # Kitchen counter along one wall
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="kitchen_counter",
                    x=round(0.5, 2),
                    y=round(0.5, 2),
                    width=round(w - 1.0, 2),
                    length=2.5,
                    rotation=0
                ))
            elif r_type in ["attached_bath", "powder_room"]:
                # Commode & Sink
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="commode",
                    x=round(1.0, 2),
                    y=round(1.0, 2),
                    width=2.0,
                    length=2.5,
                    rotation=0
                ))
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="sink",
                    x=round(w - 2.5, 2),
                    y=round(1.0, 2),
                    width=2.0,
                    length=1.5,
                    rotation=0
                ))
            elif r_type == "garage":
                r.furniture.append(FurnitureItem(
                    id=str(uuid.uuid4())[:8],
                    type="car",
                    x=round((w - 7.0) / 2, 2) if w >= 7.0 else 0.5,
                    y=round((l - 15.0) / 2, 2) if l >= 15.0 else 0.5,
                    width=min(7.0, w - 1.0),
                    length=min(15.0, l - 1.0),
                    rotation=0
                ))

        return rooms
