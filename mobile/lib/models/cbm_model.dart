class CbmSite {
  final double plotWidth;
  final double plotLength;
  final String unit;
  final double? marlaSize;
  final double? totalAreaSqft;
  final Map<String, double> setbacks;

  CbmSite({
    required this.plotWidth,
    required this.plotLength,
    this.unit = 'feet',
    this.marlaSize,
    this.totalAreaSqft,
    Map<String, double>? setbacks,
  }) : setbacks = setbacks ?? {'front': 6.0, 'rear': 6.0, 'left': 3.0, 'right': 3.0};

  factory CbmSite.fromJson(Map<String, dynamic> json) {
    return CbmSite(
      plotWidth: (json['plot_width'] as num?)?.toDouble() ?? 50.0,
      plotLength: (json['plot_length'] as num?)?.toDouble() ?? 60.0,
      unit: json['unit'] ?? 'feet',
      marlaSize: (json['marla_size'] as num?)?.toDouble(),
      totalAreaSqft: (json['total_area_sqft'] as num?)?.toDouble(),
      setbacks: (json['setbacks'] as Map?)?.map((k, v) => MapEntry(k.toString(), (v as num).toDouble())) ?? {'front': 6.0, 'rear': 6.0, 'left': 3.0, 'right': 3.0},
    );
  }

  Map<String, dynamic> toJson() => {
    'plot_width': plotWidth,
    'plot_length': plotLength,
    'unit': unit,
    if (marlaSize != null) 'marla_size': marlaSize,
    if (totalAreaSqft != null) 'total_area_sqft': totalAreaSqft,
    'setbacks': setbacks,
  };
}

class CbmBuildingLevel {
  final String levelId;
  final int index;
  final String name;
  final double elevation;
  final double height;
  final double slabThickness;

  CbmBuildingLevel({
    required this.levelId,
    required this.index,
    required this.name,
    this.elevation = 0.0,
    this.height = 11.0,
    this.slabThickness = 0.75,
  });

  factory CbmBuildingLevel.fromJson(Map<String, dynamic> json) {
    return CbmBuildingLevel(
      levelId: json['level_id'] ?? 'lvl_0',
      index: (json['index'] as num?)?.toInt() ?? 0,
      name: json['name'] ?? 'Ground Floor',
      elevation: (json['elevation'] as num?)?.toDouble() ?? 0.0,
      height: (json['height'] as num?)?.toDouble() ?? 11.0,
      slabThickness: (json['slab_thickness'] as num?)?.toDouble() ?? 0.75,
    );
  }

  Map<String, dynamic> toJson() => {
    'level_id': levelId,
    'index': index,
    'name': name,
    'elevation': elevation,
    'height': height,
    'slab_thickness': slabThickness,
  };
}

class CbmWallSegment {
  final String id;
  final String levelId;
  final List<double> start;
  final List<double> end;
  final double thickness;
  final String wallType;
  final String material;

  CbmWallSegment({
    required this.id,
    required this.levelId,
    required this.start,
    required this.end,
    this.thickness = 0.75,
    this.wallType = 'exterior',
    this.material = 'brick_masonry',
  });

  factory CbmWallSegment.fromJson(Map<String, dynamic> json) {
    final startList = (json['start'] as List?)?.map((e) => (e as num).toDouble()).toList() ?? [0.0, 0.0];
    final endList = (json['end'] as List?)?.map((e) => (e as num).toDouble()).toList() ?? [0.0, 0.0];
    return CbmWallSegment(
      id: json['id'] ?? '',
      levelId: json['level_id'] ?? 'lvl_0',
      start: startList,
      end: endList,
      thickness: (json['thickness'] as num?)?.toDouble() ?? 0.75,
      wallType: json['wall_type'] ?? 'exterior',
      material: json['material'] ?? 'brick_masonry',
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'level_id': levelId,
    'start': start,
    'end': end,
    'thickness': thickness,
    'wall_type': wallType,
    'material': material,
  };
}

class CbmRoomPolygon {
  final String id;
  final String levelId;
  final String name;
  final String roomType;
  final List<List<double>> polygon;
  final double areaSqft;
  final String? color;
  final double? ceilingHeight;

  CbmRoomPolygon({
    required this.id,
    required this.levelId,
    required this.name,
    required this.roomType,
    required this.polygon,
    required this.areaSqft,
    this.color,
    this.ceilingHeight,
  });

  factory CbmRoomPolygon.fromJson(Map<String, dynamic> json) {
    final polyRaw = json['polygon'] as List? ?? [];
    final polyList = polyRaw.map((pt) {
      if (pt is List) {
        return pt.map((e) => (e as num).toDouble()).toList();
      }
      return [0.0, 0.0];
    }).toList();

    return CbmRoomPolygon(
      id: json['id'] ?? '',
      levelId: json['level_id'] ?? 'lvl_0',
      name: json['name'] ?? 'Room',
      roomType: json['room_type'] ?? 'bedroom',
      polygon: polyList,
      areaSqft: (json['area_sqft'] as num?)?.toDouble() ?? 0.0,
      color: json['color']?.toString(),
      ceilingHeight: (json['ceiling_height'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'level_id': levelId,
    'name': name,
    'room_type': roomType,
    'polygon': polygon,
    'area_sqft': areaSqft,
    if (color != null) 'color': color,
    if (ceilingHeight != null) 'ceiling_height': ceilingHeight,
  };
}

class CanonicalBuildingModelData {
  final String schemaVersion;
  final String projectId;
  final String title;
  final String? description;
  final CbmSite site;
  final List<CbmBuildingLevel> levels;
  final List<CbmWallSegment> walls;
  final List<CbmRoomPolygon> rooms;
  final List<Map<String, dynamic>> openings;
  final List<Map<String, dynamic>> slabs;
  final List<Map<String, dynamic>> stairs;
  final Map<String, dynamic>? materialEstimate;
  final Map<String, dynamic> metadata;

  CanonicalBuildingModelData({
    this.schemaVersion = '1.0.0',
    required this.projectId,
    required this.title,
    this.description,
    required this.site,
    required this.levels,
    required this.walls,
    required this.rooms,
    this.openings = const [],
    this.slabs = const [],
    this.stairs = const [],
    this.materialEstimate,
    Map<String, dynamic>? metadata,
  }) : metadata = metadata ?? {};

  factory CanonicalBuildingModelData.fromJson(Map<String, dynamic> json) {
    return CanonicalBuildingModelData(
      schemaVersion: json['schema_version'] ?? '1.0.0',
      projectId: json['project_id'] ?? 'proj_default',
      title: json['title'] ?? 'Building Project',
      description: json['description']?.toString(),
      site: CbmSite.fromJson(json['site'] is Map ? Map<String, dynamic>.from(json['site']) : {}),
      levels: (json['levels'] as List? ?? []).map((l) => CbmBuildingLevel.fromJson(Map<String, dynamic>.from(l))).toList(),
      walls: (json['walls'] as List? ?? []).map((w) => CbmWallSegment.fromJson(Map<String, dynamic>.from(w))).toList(),
      rooms: (json['rooms'] as List? ?? []).map((r) => CbmRoomPolygon.fromJson(Map<String, dynamic>.from(r))).toList(),
      openings: (json['openings'] as List? ?? []).map((o) => Map<String, dynamic>.from(o)).toList(),
      slabs: (json['slabs'] as List? ?? []).map((s) => Map<String, dynamic>.from(s)).toList(),
      stairs: (json['stairs'] as List? ?? []).map((st) => Map<String, dynamic>.from(st)).toList(),
      materialEstimate: json['material_estimate'] is Map ? Map<String, dynamic>.from(json['material_estimate']) : null,
      metadata: json['metadata'] is Map ? Map<String, dynamic>.from(json['metadata']) : {},
    );
  }

  Map<String, dynamic> toJson() => {
    'schema_version': schemaVersion,
    'project_id': projectId,
    'title': title,
    if (description != null) 'description': description,
    'site': site.toJson(),
    'levels': levels.map((l) => l.toJson()).toList(),
    'walls': walls.map((w) => w.toJson()).toList(),
    'rooms': rooms.map((r) => r.toJson()).toList(),
    'openings': openings,
    'slabs': slabs,
    'stairs': stairs,
    if (materialEstimate != null) 'material_estimate': materialEstimate,
    'metadata': metadata,
  };
}
