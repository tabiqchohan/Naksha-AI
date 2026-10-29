import 'package:flutter/material.dart';

class RoomModel {
  final String id;
  final String name;
  final String type;
  double x;
  double y;
  double width;
  double length;
  final Color color;

  RoomModel({
    required this.id,
    required this.name,
    required this.type,
    required this.x,
    required this.y,
    required this.width,
    required this.length,
    required this.color,
  });

  double get sqft => width * length;

  factory RoomModel.fromJson(Map<String, dynamic> json) {
    return RoomModel(
      id: json['id'] ?? '',
      name: json['name'] ?? 'Room',
      type: json['type'] ?? 'bedroom',
      x: (json['x'] as num).toDouble(),
      y: (json['y'] as num).toDouble(),
      width: (json['width'] as num).toDouble(),
      length: (json['length'] as num).toDouble(),
      color: Colors.blueAccent,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'type': type,
    'x': x,
    'y': y,
    'width': width,
    'length': length,
  };
}

class PlotModel {
  final double width;
  final double length;
  final String unit;

  PlotModel({
    required this.width,
    required this.length,
    this.unit = 'feet',
  });

  double get totalSqft => width * length;
  double get marla => totalSqft / 225.0;

  factory PlotModel.fromJson(Map<String, dynamic> json) {
    return PlotModel(
      width: (json['width'] as num).toDouble(),
      length: (json['length'] as num).toDouble(),
      unit: json['unit'] ?? 'feet',
    );
  }
}
