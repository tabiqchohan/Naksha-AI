import 'package:flutter/material.dart';
import '../models/floor_plan_model.dart';

class FloorPlanPainter extends CustomPainter {
  final PlotModel plot;
  final List<RoomModel> rooms;
  final String? selectedRoomId;

  FloorPlanPainter({
    required this.plot,
    required this.rooms,
    this.selectedRoomId,
  });

  @override
  void paint(Canvas canvas, Size size) {
    // 1. Grid Background
    final gridPaint = Paint()
      ..color = const Color(0xFFE2E8F0)
      ..strokeWidth = 0.5;

    for (double x = 0; x < size.width; x += 20) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), gridPaint);
    }
    for (double y = 0; y < size.height; y += 20) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), gridPaint);
    }

    // Scale calculation
    final scale = (size.width - 60) / plot.width;
    const originX = 30.0;
    const originY = 30.0;

    final plotWidthPx = plot.width * scale;
    final plotHeightPx = plot.length * scale;

    // 2. Plot Boundary
    final plotPaint = Paint()
      ..color = const Color(0xFF1E3A8A)
      ..strokeWidth = 3.0
      ..style = PaintingStyle.stroke;

    final plotFill = Paint()
      ..color = Colors.white
      ..style = PaintingStyle.fill;

    final plotRect = Rect.fromLTWH(originX, originY, plotWidthPx, plotHeightPx);
    canvas.drawRect(plotRect, plotFill);
    canvas.drawRect(plotRect, plotPaint);

    // 3. Dimension Lines (Top 50ft & Left 60ft)
    final dimPaint = Paint()
      ..color = const Color(0xFF2563EB)
      ..strokeWidth = 1.5;

    // Top
    canvas.drawLine(const Offset(originX, 15), Offset(originX + plotWidthPx, 15), dimPaint);
    _drawText(canvas, '${plot.width.toInt()}ft', Offset(originX + plotWidthPx / 2, 5), Colors.blue[900]!, 12, true);

    // Left
    canvas.drawLine(const Offset(15, originY), Offset(15, originY + plotHeightPx), dimPaint);

    // 4. Draw Rooms
    for (final room in rooms) {
      final rx = originX + room.x * scale;
      final ry = originY + room.y * scale;
      final rw = room.width * scale;
      final rl = room.length * scale;
      final isSelected = selectedRoomId == room.id;

      final roomRect = Rect.fromLTWH(rx, ry, rw, rl);

      // Room Fill
      final roomFillPaint = Paint()
        ..color = isSelected ? const Color(0xFFEFF6FF) : const Color(0xFFF8FAFC)
        ..style = PaintingStyle.fill;
      canvas.drawRect(roomRect, roomFillPaint);

      // Room Walls
      final roomWallPaint = Paint()
        ..color = isSelected ? const Color(0xFF2563EB) : const Color(0xFF0F172A)
        ..strokeWidth = isSelected ? 2.5 : 2.0
        ..style = PaintingStyle.stroke;
      canvas.drawRect(roomRect, roomWallPaint);

      // Draw Furniture hints
      _drawFurnitureHint(canvas, room, rx, ry, rw, rl);

      // Room Name Text
      _drawText(
        canvas,
        room.name.toUpperCase(),
        Offset(rx + rw / 2, ry + rl / 2 - 6),
        const Color(0xFF0F172A),
        10,
        true,
      );

      // Room SqFt Text
      _drawText(
        canvas,
        '${room.sqft.toInt()} sq ft',
        Offset(rx + rw / 2, ry + rl / 2 + 8),
        const Color(0xFF64748B),
        9,
        false,
      );
    }
  }

  void _drawFurnitureHint(Canvas canvas, RoomModel room, double rx, double ry, double rw, double rl) {
    final paint = Paint()
      ..color = const Color(0xFFCBD5E1)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    if (room.type.contains('bedroom')) {
      // Bed box
      final bedRect = Rect.fromLTWH(rx + rw * 0.3, ry + 6, rw * 0.4, rl * 0.45);
      canvas.drawRect(bedRect, paint);
    } else if (room.type.contains('kitchen')) {
      // Counter
      final counter = Path()
        ..moveTo(rx + 4, ry + 4)
        ..lineTo(rx + rw - 4, ry + 4)
        ..lineTo(rx + rw - 4, ry + 16)
        ..lineTo(rx + 16, ry + 16)
        ..lineTo(rx + 16, ry + rl - 4)
        ..lineTo(rx + 4, ry + rl - 4)
        ..close();
      canvas.drawPath(counter, paint);
    }
  }

  void _drawText(Canvas canvas, String text, Offset center, Color color, double fontSize, bool isBold) {
    final textSpan = TextSpan(
      text: text,
      style: TextStyle(
        color: color,
        fontSize: fontSize,
        fontWeight: isBold ? FontWeight.bold : FontWeight.normal,
      ),
    );
    final textPainter = TextPainter(
      text: textSpan,
      textDirection: TextDirection.ltr,
    );
    textPainter.layout();
    textPainter.paint(canvas, Offset(center.dx - textPainter.width / 2, center.dy - textPainter.height / 2));
  }

  @override
  bool shouldRepaint(covariant FloorPlanPainter oldDelegate) => true;
}
