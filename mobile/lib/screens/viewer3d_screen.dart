import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import '../services/language_service.dart';

class Viewer3DScreen extends StatefulWidget {
  final Map<String, dynamic>? plan;
  final String? webViewerUrl;
  const Viewer3DScreen({super.key, this.plan, this.webViewerUrl});

  @override
  State<Viewer3DScreen> createState() => _Viewer3DScreenState();
}

class _Viewer3DScreenState extends State<Viewer3DScreen> {
  WebViewController? _controller;
  bool loading = true;

  double _rotation = 0;
  double _zoom = 1;
  Offset _pan = Offset.zero;
  int _selectedFloor = -1;

  double _startZoom = 1;
  Offset _startPan = Offset.zero;
  Offset _startFocal = Offset.zero;
  double _startRotation = 0;

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

  int _floorOf(Map<String, dynamic> room) => (room['floor_level'] as num? ?? 0).toInt();

  int get _storeys {
    final maxRoomFloor = _rooms.fold<int>(0, (m, r) => math.max(m, _floorOf(r)));
    final declared = _floors.isEmpty ? 1 : _floors.length;
    return math.max(declared, maxRoomFloor + 1);
  }

  void _resetView() {
    setState(() {
      _rotation = 0;
      _zoom = 1;
      _pan = Offset.zero;
    });
  }

  void _rotate(double delta) => setState(() => _rotation += delta);

  void _zoomBy(double factor) => setState(() => _zoom = (_zoom * factor).clamp(0.5, 3.0));

  void _onScaleStart(ScaleStartDetails details) {
    _startZoom = _zoom;
    _startPan = _pan;
    _startFocal = details.localFocalPoint;
    _startRotation = _rotation;
  }

  void _onScaleUpdate(ScaleUpdateDetails details) {
    setState(() {
      _zoom = (_startZoom * details.scale).clamp(0.5, 3.0);
      _rotation = _startRotation + details.rotation;
      _pan = _startPan + (details.localFocalPoint - _startFocal);
    });
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    final visibleRooms = _selectedFloor < 0 ? _rooms : _rooms.where((r) => _floorOf(r) == _selectedFloor).toList();
    final plot = widget.plan?['plot'] is Map ? Map<String, dynamic>.from(widget.plan!['plot'] as Map) : const <String, dynamic>{};

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFF0F172A)),
        title: Text(lang.t('3D Concept Viewer', 'تھری ڈی تصوراتی ویور'), style: const TextStyle(color: Color(0xFF0F172A))),
        actions: [
          IconButton(onPressed: _resetView, tooltip: lang.t('Reset view', 'منظر ری سیٹ کریں'), icon: const Icon(Icons.restart_alt)),
        ],
      ),
      body: _controller != null
          ? Stack(children: [WebViewWidget(controller: _controller!), if (loading) const Center(child: CircularProgressIndicator())])
          : Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(color: const Color(0xFFEFF6FF), border: Border.all(color: const Color(0xFFBFDBFE)), borderRadius: BorderRadius.circular(12)),
                  child: Text(lang.t(
                    'Isometric concept preview generated from the current plan. Technical 3D/model coordination requires a licensed architect/engineer.',
                    'موجودہ پلان سے تیار کردہ آئیسومیٹرک تصوراتی پیش نظارہ۔ تکنیکی تھری ڈی/ماڈل کوآرڈینیشن کے لیے لائسنس یافتہ آرکیٹیکٹ/انجینئر ضروری ہے۔',
                  ), style: const TextStyle(fontSize: 12)),
                ),
                const SizedBox(height: 12),
                _PlanStats(rooms: visibleRooms, plot: widget.plan?['plot'], storeys: _storeys, isUrdu: lang.isUrdu),
                const SizedBox(height: 12),
                if (_storeys > 1)
                  SizedBox(
                    height: 38,
                    child: ListView(
                      scrollDirection: Axis.horizontal,
                      children: [
                        _floorChip(lang, -1, lang.t('All', 'سب')),
                        for (var f = 0; f < _storeys; f++)
                          _floorChip(lang, f, f == 0 ? lang.t('Ground', 'گراؤنڈ') : 'G+$f'),
                      ],
                    ),
                  ),
                if (_storeys > 1) const SizedBox(height: 8),
                Expanded(
                  child: Container(
                    width: double.infinity,
                    decoration: BoxDecoration(color: const Color(0xFF0F172A), borderRadius: BorderRadius.circular(12)),
                    clipBehavior: Clip.antiAlias,
                    child: _rooms.isEmpty
                        ? Center(child: Text(lang.t('No rooms available. Generate or open a plan first.', 'کوئی کمرہ دستیاب نہیں۔ پہلے پلان بنائیں یا کھولیں۔'), style: const TextStyle(color: Colors.white70)))
                        : Stack(
                            children: [
                              Positioned.fill(
                                child: GestureDetector(
                                  behavior: HitTestBehavior.opaque,
                                  onScaleStart: _onScaleStart,
                                  onScaleUpdate: _onScaleUpdate,
                                  child: CustomPaint(
                                    painter: _IsoPainter(
                                      rooms: visibleRooms,
                                      plot: plot,
                                      rotation: _rotation,
                                      zoom: _zoom,
                                      pan: _pan,
                                      showAllFloors: _selectedFloor < 0,
                                      floorOf: _floorOf,
                                    ),
                                  ),
                                ),
                              ),
                              Positioned(
                                left: 10,
                                top: 10,
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                  decoration: BoxDecoration(color: Colors.black.withValues(alpha: 0.45), borderRadius: BorderRadius.circular(8)),
                                  child: Text(lang.t('Drag to pan - pinch to zoom - twist to rotate', 'پین کے لیے کھینچیں - زوم کے لیے پنچ کریں - گھمانے کے لیے موڑیں'), style: const TextStyle(color: Colors.white70, fontSize: 9)),
                                ),
                              ),
                              Positioned(
                                right: 10,
                                bottom: 10,
                                child: Column(
                                  children: [
                                    _controlButton(Icons.rotate_left, lang.t('Rotate left', 'بائیں گھمائیں'), () => _rotate(-math.pi / 12)),
                                    const SizedBox(height: 6),
                                    _controlButton(Icons.rotate_right, lang.t('Rotate right', 'دائیں گھمائیں'), () => _rotate(math.pi / 12)),
                                    const SizedBox(height: 10),
                                    _controlButton(Icons.add, lang.t('Zoom in', 'زوم ان'), () => _zoomBy(1.2)),
                                    const SizedBox(height: 6),
                                    _controlButton(Icons.remove, lang.t('Zoom out', 'زوم آؤٹ'), () => _zoomBy(1 / 1.2)),
                                    const SizedBox(height: 10),
                                    _controlButton(Icons.center_focus_strong, lang.t('Reset view', 'منظر ری سیٹ کریں'), _resetView),
                                  ],
                                ),
                              ),
                            ],
                          ),
                  ),
                ),
                const SizedBox(height: 8),
                ExpansionTile(
                  tilePadding: EdgeInsets.zero,
                  title: Text(lang.t('Plan JSON', 'پلان جے سون'), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
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
                Text(lang.t(
                  'Concept only. Verify design, bylaws, structure, MEP, and dimensions with licensed professionals.',
                  'صرف تصور۔ ڈیزائن، بلدیاتی قوانین، اسٹرکچر، ایم ای پی اور پیمائش کی لائسنس یافتہ پیشہ ور افراد سے تصدیق کریں۔',
                ), style: const TextStyle(fontSize: 11, color: Color(0xFF9A3412))),
              ]),
            ),
    );
  }

  Widget _floorChip(LanguageService lang, int floor, String label) {
    final selected = _selectedFloor == floor;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(label, style: TextStyle(fontSize: 12, color: selected ? Colors.white : const Color(0xFF334155))),
        selected: selected,
        onSelected: (_) => setState(() => _selectedFloor = floor),
        selectedColor: const Color(0xFF2563EB),
        backgroundColor: Colors.white,
      ),
    );
  }

  Widget _controlButton(IconData icon, String tooltip, VoidCallback onPressed) {
    return Tooltip(
      message: tooltip,
      child: Material(
        color: Colors.white.withValues(alpha: 0.92),
        shape: const CircleBorder(),
        child: InkWell(
          onTap: onPressed,
          customBorder: const CircleBorder(),
          child: SizedBox(width: 38, height: 38, child: Icon(icon, size: 20, color: const Color(0xFF0F172A))),
        ),
      ),
    );
  }
}

class _PlanStats extends StatelessWidget {
  final List<Map<String, dynamic>> rooms;
  final dynamic plot;
  final int storeys;
  final bool isUrdu;
  const _PlanStats({required this.rooms, required this.plot, required this.storeys, required this.isUrdu});

  @override
  Widget build(BuildContext context) {
    final covered = rooms.fold<double>(0, (sum, r) => sum + ((r['width'] as num? ?? 0) * (r['length'] as num? ?? 0)).toDouble());
    final width = plot is Map ? (plot['width'] as num? ?? 0) : 0;
    final length = plot is Map ? (plot['length'] as num? ?? 0) : 0;
    String t(String en, String ur) => isUrdu ? ur : en;
    final items = <(IconData, String, String)>[
      (Icons.meeting_room_outlined, t('Rooms', 'کمرے'), '${rooms.length}'),
      (Icons.square_foot, t('Covered', 'ڈھکا رقبہ'), '${covered.round()} sqft'),
      (Icons.crop_square, t('Plot', 'پلاٹ'), '${width.toStringAsFixed(0)}x${length.toStringAsFixed(0)} ft'),
      (Icons.layers_outlined, t('Storeys', 'منزلیں'), '$storeys'),
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
  final double rotation;
  final double zoom;
  final Offset pan;
  final bool showAllFloors;
  final int Function(Map<String, dynamic>) floorOf;

  _IsoPainter({
    required this.rooms,
    required this.plot,
    required this.rotation,
    required this.zoom,
    required this.pan,
    required this.showAllFloors,
    required this.floorOf,
  });

  static const double _wall = 9.0;
  static const double _floorHeight = 12.0;
  static const double _angle = math.pi / 6;

  double _isoX(double x, double y) => (x - y) * math.cos(_angle);
  double _isoY(double x, double y, double z) => (x + y) * math.sin(_angle) - z;

  @override
  void paint(Canvas canvas, Size size) {
    final plotW = (plot['width'] as num? ?? 50).toDouble();
    final plotL = (plot['length'] as num? ?? 60).toDouble();
    final diameter = math.sqrt(plotW * plotW + plotL * plotL) + 4;
    final topFloor = showAllFloors ? rooms.fold<int>(0, (m, r) => math.max(m, floorOf(r))) : 0;
    final wallTop = _wall + topFloor * _floorHeight;

    final corners = <Offset>[
      for (final x in [-2.0, diameter])
        for (final y in [-2.0, diameter])
          for (final z in [0.0, wallTop])
            Offset(_isoX(x, y), _isoY(x, y, z)),
    ];
    final minX = corners.map((c) => c.dx).reduce(math.min);
    final maxX = corners.map((c) => c.dx).reduce(math.max);
    final minY = corners.map((c) => c.dy).reduce(math.min);
    final maxY = corners.map((c) => c.dy).reduce(math.max);
    final spanX = math.max(maxX - minX, 1.0);
    final spanY = math.max(maxY - minY, 1.0);

    final panInPlan = Offset(pan.dx / zoom, pan.dy / zoom);
    final fitScale = math.min(size.width / spanX, size.height / spanY) * 0.82;
    final scale = fitScale * zoom;
    final originX = (size.width - spanX * scale) / 2 - minX * scale + panInPlan.dx * zoom;
    final originY = (size.height - spanY * scale) / 2 - minY * scale + panInPlan.dy * zoom;

    final cosR = math.cos(rotation);
    final sinR = math.sin(rotation);
    final cx = plotW / 2;
    final cy = plotL / 2;

    Offset rotate(double x, double y) {
      final dx = x - cx;
      final dy = y - cy;
      return Offset(cx + dx * cosR - dy * sinR, cy + dx * sinR + dy * cosR);
    }

    Offset project(double x, double y, double z) {
      final p = rotate(x, y);
      return Offset(originX + _isoX(p.dx, p.dy) * scale, originY + _isoY(p.dx, p.dy, z) * scale);
    }

    _drawPlot(canvas, project, plotW, plotL);

    final ordered = [...rooms]..sort((a, b) {
        final floorDiff = floorOf(a).compareTo(floorOf(b));
        if (floorDiff != 0) return floorDiff;
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
      final zBase = showAllFloors ? floorOf(room) * _floorHeight : 0.0;
      _drawRoom(canvas, project, room, x, y, w, l, scale, zBase);
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

  void _drawRoom(Canvas canvas, Offset Function(double, double, double) project, Map<String, dynamic> room, double x, double y, double w, double l, double scale, double zBase) {
    final base = _roomColor(room['type']?.toString() ?? '');
    final top = base.withValues(alpha: 0.95);
    final left = base.withValues(alpha: 0.72);
    final right = base.withValues(alpha: 0.52);
    final edge = Paint()..color = const Color(0xFF0F172A).withValues(alpha: 0.8)..style = PaintingStyle.stroke..strokeWidth = 0.8;
    final zTop = zBase + _wall;

    final f00 = project(x, y, zBase), f10 = project(x + w, y, zBase), f11 = project(x + w, y + l, zBase), f01 = project(x, y + l, zBase);
    final t00 = project(x, y, zTop), t10 = project(x + w, y, zTop), t11 = project(x + w, y + l, zTop), t01 = project(x, y + l, zTop);

    _polygon(canvas, [f10, f11, t11, t10], right, edge);
    _polygon(canvas, [f01, f11, t11, t01], left, edge);
    _polygon(canvas, [f00, f10, f11, f01], base.withValues(alpha: 0.35), edge);
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
  bool shouldRepaint(covariant _IsoPainter oldDelegate) =>
      oldDelegate.rooms != rooms ||
      oldDelegate.plot != plot ||
      oldDelegate.rotation != rotation ||
      oldDelegate.zoom != zoom ||
      oldDelegate.pan != pan ||
      oldDelegate.showAllFloors != showAllFloors;
}
