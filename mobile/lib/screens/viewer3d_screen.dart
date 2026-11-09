import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class Viewer3DScreen extends StatefulWidget {
  final Map<String, dynamic>? plan;
  final String? webViewerUrl; // optional deployed web app URL with 3D support
  const Viewer3DScreen({super.key, this.plan, this.webViewerUrl});

  @override
  State<Viewer3DScreen> createState() => _Viewer3DScreenState();
}

class _Viewer3DScreenState extends State<Viewer3DScreen> {
  WebViewController? _controller;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    final url = widget.webViewerUrl;
    if (url != null && url.isNotEmpty) {
      final c = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..setNavigationDelegate(NavigationDelegate(onPageFinished: (_) => setState(() => loading = false)))
        ..loadRequest(Uri.parse(url));
      _controller = c;
    } else {
      loading = false;
    }
  }

  List<Map<String, dynamic>> get _rooms {
    final raw = widget.plan?['rooms'];
    if (raw is! List) return [];
    return raw.whereType<Map>().map((r) => Map<String, dynamic>.from(r)).toList();
  }

  List<Map<String, dynamic>> get _floors {
    final raw = widget.plan?['floors'];
    if (raw is List) return raw.whereType<Map>().map((f) => Map<String, dynamic>.from(f)).toList();
    return [];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFF0F172A)),
        title: const Text('3D Concept Viewer', style: TextStyle(color: Color(0xFF0F172A))),
      ),
      body: _controller != null
          ? Stack(children: [WebViewWidget(controller: _controller!), if (loading) const Center(child: CircularProgressIndicator())])
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: const Color(0xFFEFF6FF), border: Border.all(color: const Color(0xFFBFDBFE)), borderRadius: BorderRadius.circular(12)),
                  child: const Text('Isometric concept preview generated from the current plan. Technical 3D/model coordination requires a licensed architect/engineer.', style: TextStyle(fontSize: 12)),
                ),
                const SizedBox(height: 12),
                _PlanStats(rooms: _rooms, plot: widget.plan?['plot'], floors: _floors),
                const SizedBox(height: 12),
                Expanded(
                  child: Container(
                    width: double.infinity,
                    decoration: BoxDecoration(color: const Color(0xFF0F172A), borderRadius: BorderRadius.circular(12)),
                    clipBehavior: Clip.antiAlias,
                    child: _rooms.isEmpty
                        ? const Center(child: Text('No rooms available. Generate or open a plan first.', style: TextStyle(color: Colors.white70)))
                        : CustomPaint(painter: _IsoPainter(rooms: _rooms, plot: widget.plan?['plot'] is Map ? Map<String, dynamic>.from(widget.plan!['plot'] as Map) : const {})),
                  ),
                ),
                const SizedBox(height: 8),
                ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  title: const Text('Plan JSON', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                  children: [
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
                      child: SingleChildScrollView(
                        child: Text(const JsonEncoder.withIndent('  ').convert(widget.plan ?? {'message': 'No plan loaded'}), style: const TextStyle(fontSize: 11, fontFamily: 'monospace')),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                const Text('Concept only. Verify design, bylaws, structure, MEP, and dimensions with licensed professionals.', style: TextStyle(fontSize: 11, color: Color(0xFF9A3412))),
              ]),
            ),
    );
  }
}

class _PlanStats extends StatelessWidget {
  final List<Map<String, dynamic>> rooms;
  final dynamic plot;
  final List<Map<String, dynamic>> floors;
  const _PlanStats({required this.rooms, required this.plot, required this.floors});

  @override
  Widget build(BuildContext context) {
    final covered = rooms.fold<double>(0, (sum, r) => sum + ((r['width'] as num? ?? 0) * (r['length'] as num? ?? 0)).toDouble());
    final width = plot is Map ? (plot['width'] as num? ?? 0) : 0;
    final length = plot is Map ? (plot['length'] as num? ?? 0) : 0;
    final items = <(IconData, String, String)>[
      (Icons.meeting_room_outlined, 'Rooms', '${rooms.length}'),
      (Icons.square_foot, 'Covered', '${covered.round()} sqft'),
      (Icons.crop_square, 'Plot', '${width.toStringAsFixed(0)}x${length.toStringAsFixed(0)} ft'),
      (Icons.layers_outlined, 'Storeys', '${floors.isEmpty ? 1 : floors.length}'),
    ];
    return Wrap(spacing: 8, runSpacing: 8, children: items.map((item) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE2E8F0))),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(item.$1, size: 14, color: const Color(0xFF2563EB)),
          const SizedBox(width: 6),
          Text('${item.$2}: ', style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
          Text(item.$3, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF0F172A))),
        ]),
      );
    }).toList());
  }
}

class _IsoPainter extends CustomPainter {
  final List<Map<String, dynamic>> rooms;
  final Map<String, dynamic> plot;
  _IsoPainter({required this.rooms, required this.plot});

  static const double _wall = 9.0;
  static const double _angle = math.pi / 6;

  double _isoX(double x, double y) => (x - y) * math.cos(_angle);
  double _isoY(double x, double y, double z) => (x + y) * math.sin(_angle) - z;

  @override
  void paint(Canvas canvas, Size size) {
    final plotW = (plot['width'] as num? ?? 50).toDouble();
    final plotL = (plot['length'] as num? ?? 60).toDouble();

    final corners = <Offset>[
      for (final x in [0.0, plotW])
        for (final y in [0.0, plotL])
          for (final z in [0.0, _wall]) Offset(_isoX(x, y), _isoY(x, y, z)),
    ];
    final minX = corners.map((c) => c.dx).reduce(math.min);
    final maxX = corners.map((c) => c.dx).reduce(math.max);
    final minY = corners.map((c) => c.dy).reduce(math.min);
    final maxY = corners.map((c) => c.dy).reduce(math.max);
    final spanX = math.max(maxX - minX, 1.0);
    final spanY = math.max(maxY - minY, 1.0);
    final scale = math.min(size.width / spanX, size.height / spanY) * 0.82;
    final originX = (size.width - spanX * scale) / 2 - minX * scale;
    final originY = (size.height - spanY * scale) / 2 - minY * scale;

    Offset project(double x, double y, double z) => Offset(originX + _isoX(x, y) * scale, originY + _isoY(x, y, z) * scale);

    _drawPlot(canvas, project, plotW, plotL);

    final ordered = [...rooms]..sort((a, b) {
        final da = (a['x'] as num? ?? 0) + (a['y'] as num? ?? 0);
        final db = (b['x'] as num? ?? 0) + (b['y'] as num? ?? 0);
        return da.compareTo(db);
      });

    for (final room in ordered) {
      final x = (room['x'] as num? ?? 0).toDouble();
      final y = (room['y'] as num? ?? 0).toDouble();
      final w = (room['width'] as num? ?? 0).toDouble();
      final l = (room['length'] as num? ?? 0).toDouble();
      if (w <= 0 || l <= 0) continue;
      _drawRoom(canvas, project, room, x, y, w, l, scale);
    }
  }

  void _drawPlot(Canvas canvas, Offset Function(double, double, double) project, double w, double l) {
    final pts = [project(0, 0, 0), project(w, 0, 0), project(w, l, 0), project(0, l, 0)];
    final path = Path()..moveTo(pts[0].dx, pts[0].dy);
    for (final p in pts.skip(1)) {
      path.lineTo(p.dx, p.dy);
    }
    path.close();
    canvas.drawPath(path, Paint()..color = const Color(0xFF1E293B)..style = PaintingStyle.fill);
    canvas.drawPath(path, Paint()..color = const Color(0xFF38BDF8)..style = PaintingStyle.stroke..strokeWidth = 1.4);
  }

  void _drawRoom(Canvas canvas, Offset Function(double, double, double) project, Map<String, dynamic> room, double x, double y, double w, double l, double scale) {
    final base = _roomColor(room['type']?.toString() ?? '');
    final top = base.withValues(alpha: 0.95);
    final left = base.withValues(alpha: 0.72);
    final right = base.withValues(alpha: 0.52);
    final edge = Paint()..color = const Color(0xFF0F172A).withValues(alpha: 0.8)..style = PaintingStyle.stroke..strokeWidth = 0.8;

    final f10 = project(x + w, y, 0), f11 = project(x + w, y + l, 0), f01 = project(x, y + l, 0);
    final t00 = project(x, y, _wall), t10 = project(x + w, y, _wall), t11 = project(x + w, y + l, _wall), t01 = project(x, y + l, _wall);

    _polygon(canvas, [f10, f11, t11, t10], right, edge);
    _polygon(canvas, [f01, f11, t11, t01], left, edge);
    _polygon(canvas, [t00, t10, t11, t01], top, edge);

    if (scale > 2.2) {
      final center = Offset((t00.dx + t11.dx) / 2, (t00.dy + t11.dy) / 2);
      final label = (room['name'] ?? room['type'] ?? 'Room').toString();
      final tp = TextPainter(
        text: TextSpan(text: label.length > 14 ? '${label.substring(0, 14)}…' : label, style: TextStyle(fontSize: math.max(7, math.min(11, scale * 0.9)), color: const Color(0xFF0F172A), fontWeight: FontWeight.w700)),
        textDirection: TextDirection.ltr,
        maxLines: 1,
        ellipsis: '…',
      )..layout(maxWidth: math.max(40, w * scale));
      tp.paint(canvas, Offset(center.dx - tp.width / 2, center.dy - tp.height / 2));
    }
  }

  void _polygon(Canvas canvas, List<Offset> pts, Color color, Paint edge) {
    final path = Path()..moveTo(pts.first.dx, pts.first.dy);
    for (final p in pts.skip(1)) {
      path.lineTo(p.dx, p.dy);
    }
    path.close();
    canvas.drawPath(path, Paint()..color = color..style = PaintingStyle.fill);
    canvas.drawPath(path, edge);
  }

  Color _roomColor(String type) {
    switch (type.toLowerCase()) {
      case 'master_bedroom':
        return const Color(0xFF60A5FA);
      case 'bedroom':
        return const Color(0xFF93C5FD);
      case 'kitchen':
        return const Color(0xFFFBBF24);
      case 'living_room':
      case 'drawing_room':
        return const Color(0xFFA78BFA);
      case 'attached_bath':
      case 'powder_room':
        return const Color(0xFF2DD4BF);
      case 'garage':
        return const Color(0xFF94A3B8);
      case 'lawn':
        return const Color(0xFF4ADE80);
      case 'staircase':
        return const Color(0xFFF87171);
      default:
        return const Color(0xFFCBD5E1);
    }
  }

  @override
  bool shouldRepaint(covariant _IsoPainter oldDelegate) => oldDelegate.rooms != rooms || oldDelegate.plot != plot;
}
