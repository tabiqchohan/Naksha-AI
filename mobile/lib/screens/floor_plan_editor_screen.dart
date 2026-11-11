import 'dart:io';
import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import '../models/floor_plan_model.dart';
import '../widgets/floor_plan_painter.dart';
import '../services/api_service.dart';
import '../services/language_service.dart';
import '../login_screen.dart';
import '../material_estimate_screen.dart';
import 'viewer3d_screen.dart';

class FloorPlanEditorScreen extends StatefulWidget {
  final Map<String, dynamic>? initialPlan;
  const FloorPlanEditorScreen({super.key, this.initialPlan});

  @override
  State<FloorPlanEditorScreen> createState() => _FloorPlanEditorScreenState();
}

class _FloorPlanEditorScreenState extends State<FloorPlanEditorScreen> {
  final PlotModel _plot = PlotModel(width: 50, length: 60);
  int _selectedViewIndex = 0;
  String _buildingType = 'house';
  int _floors = 1;
  String _prompt = 'Generate 3 Bed, 2 Bath open layout for 50x40 plot.';
  String _bylawsPack = 'pakistan_generic';
  bool _isGenerating = false;
  String _status = '';
  Map<String, dynamic>? _bylawsReport;
  Map<String, dynamic>? _materialEstimate;
  final List<Map<String, dynamic>> _variants = [];

  final List<RoomModel> _rooms = [
    RoomModel(id: 'r1', name: 'MASTER BED', type: 'master_bedroom', x: 0, y: 0, width: 26, length: 32, color: Colors.blue),
    RoomModel(id: 'r2', name: 'BEDROOM 2', type: 'bedroom', x: 0, y: 32, width: 26, length: 28, color: Colors.blueAccent),
    RoomModel(id: 'r3', name: 'BATH', type: 'attached_bath', x: 26, y: 0, width: 10, length: 18, color: Colors.teal),
    RoomModel(id: 'r4', name: 'KITCHEN', type: 'kitchen', x: 36, y: 0, width: 14, length: 32, color: Colors.amber),
    RoomModel(id: 'r5', name: 'LIVING ROOM', type: 'living_room', x: 26, y: 32, width: 24, length: 28, color: Colors.purple),
  ];

  @override
  void initState() {
    super.initState();
    _loadInitial();
  }

  void _loadInitial() {
    final p = widget.initialPlan;
    if (p == null) return;
    final data = p['floor_plan_data'] is Map ? Map<String, dynamic>.from(p['floor_plan_data']) : p;
    final plot = data['plot'] is Map ? data['plot'] : null;
    if (plot != null) { _plot.width = (plot['width'] as num?)?.toDouble() ?? _plot.width; _plot.length = (plot['length'] as num?)?.toDouble() ?? _plot.length; }
    final rooms = data['rooms'];
    if (rooms is List) _applyRooms(rooms);
    _bylawsReport = data['bylaws_report'] is Map ? Map<String, dynamic>.from(data['bylaws_report']) : null;
    _materialEstimate = data['material_estimate'] is Map ? Map<String, dynamic>.from(data['material_estimate']) : null;
  }

  Color _colorFor(String type) {
    if (type.contains('kitchen')) return Colors.amber;
    if (type.contains('bath')) return Colors.teal;
    if (type.contains('living') || type.contains('drawing')) return Colors.purple;
    if (type.contains('garage') || type.contains('parking')) return Colors.grey;
    if (type.contains('shop')) return Colors.orange;
    if (type.contains('stair')) return Colors.blueGrey;
    if (type.contains('master')) return Colors.blue;
    return Colors.blueAccent;
  }

  void _applyRooms(List roomsData) {
    _rooms.clear();
    for (final raw in roomsData) {
      final r = Map<String, dynamic>.from(raw as Map);
      final type = (r['type'] ?? 'bedroom').toString();
      _rooms.add(RoomModel(
        id: (r['id'] ?? 'r_${_rooms.length}').toString(),
        name: (r['name'] ?? 'Room').toString(),
        type: type,
        x: (r['x'] as num?)?.toDouble() ?? 0,
        y: (r['y'] as num?)?.toDouble() ?? 0,
        width: (r['width'] as num?)?.toDouble() ?? 10,
        length: (r['length'] as num?)?.toDouble() ?? 10,
        color: _colorFor(type),
      ));
    }
  }

  Future<bool> _ensureAuth() async {
    final lang = LanguageScope.of(context);
    final token = await ApiService.token();
    if (token != null && token.isNotEmpty) return true;
    if (!mounted) return false;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.t('Please sign in to generate/save plans (credits required).', 'پلان بنانے/محفوظ کرنے کے لیے سائن ان کریں (کریڈٹس درکار ہیں)۔'))));
    await Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
    return (await ApiService.token()) != null;
  }

  Future<void> _generatePlan({bool variants = false}) async {
    final lang = LanguageScope.of(context);
    if (!await _ensureAuth()) return;
    setState(() { _isGenerating = true; _status = variants ? lang.t('Generating 3 variants...', '3 ورژن بنائے جا رہے ہیں...') : lang.t('Generating plan...', 'پلان بنایا جا رہا ہے...'); });
    try {
      final base = {
        'prompt': _prompt,
        'plot_width': _plot.width,
        'plot_length': _plot.length,
        'building_type': _buildingType,
        'floors': _floors,
        'bedrooms': 3,
        'bathrooms': 2,
        'bylaws_pack': _bylawsPack,
      };
      if (variants) {
        final data = await ApiService.post('/plans/generate-variants', {'base': base, 'count': 3}, auth: true);
        final list = (data['variants'] as List?) ?? [];
        _variants..clear()..addAll(list.map((e) => Map<String, dynamic>.from(e as Map)));
        if (_variants.isNotEmpty) _applyPlan(_variants.first);
        _status = lang.t('Generated ${_variants.length} variants (concept).', '${_variants.length} تصوراتی ورژن بن گئے۔');
      } else {
        final data = await ApiService.post('/plans/generate', base, auth: true);
        _applyPlan(Map<String, dynamic>.from(data as Map));
        _status = lang.t('Plan generated.', 'پلان بن گیا۔');
      }
    } catch (e) {
      _status = e.toString();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${lang.t('Error', 'خرابی')}: $e')));
    } finally {
      if (mounted) setState(() => _isGenerating = false);
    }
  }

  void _applyPlan(Map<String, dynamic> data) {
    final rooms = data['rooms'];
    if (rooms is List) _applyRooms(rooms);
    _bylawsReport = data['bylaws_report'] is Map ? Map<String, dynamic>.from(data['bylaws_report']) : null;
    _materialEstimate = data['material_estimate'] is Map ? Map<String, dynamic>.from(data['material_estimate']) : _materialEstimate;
  }

  Map<String, dynamic> _currentPlanMap() => {
    'id': 'mobile-${DateTime.now().millisecondsSinceEpoch}',
    'title': 'Current Concept Plan',
    'plot': {'width': _plot.width, 'length': _plot.length, 'unit': 'feet'},
    'rooms': _rooms.map((r) => {'id': r.id, 'name': r.name, 'type': r.type, 'x': r.x, 'y': r.y, 'width': r.width, 'length': r.length}).toList(),
    'bylaws_report': _bylawsReport,
  };

  Future<void> _exportPlan(String kind) async {
    final lang = LanguageScope.of(context);
    final messenger = ScaffoldMessenger.of(context);
    try {
      final bytes = await ApiService.postBytes('/plans/export-$kind', _currentPlanMap(), auth: true);
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}${Platform.pathSeparator}nakshai_${DateTime.now().millisecondsSinceEpoch}.$kind');
      await file.writeAsBytes(bytes, flush: true);
      await OpenFilex.open(file.path);
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('${lang.t('Saved', 'محفوظ ہو گیا')}: ${file.path}')));
    } catch (e) {
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('${lang.t('Export failed', 'ایکسپورٹ ناکام')}: $e')));
    }
  }

  Future<void> _saveProject() async {
    final lang = LanguageScope.of(context);
    if (!await _ensureAuth()) return;
    try {
      await ApiService.post('/projects/save', {
        'title': 'Mobile Plan ${DateTime.now().millisecondsSinceEpoch.toString().substring(8)}',
        'building_type': _buildingType,
        'floors': _floors,
        'plot_width': _plot.width,
        'plot_length': _plot.length,
        'prompt': _prompt,
        'floor_plan_data': {'plot': {'width': _plot.width, 'length': _plot.length}, 'rooms': _rooms.map((r) => {'id': r.id, 'name': r.name, 'type': r.type, 'x': r.x, 'y': r.y, 'width': r.width, 'length': r.length}).toList(), 'bylaws_report': _bylawsReport},
      }, auth: true);
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.t('Project saved.', 'منصوبہ محفوظ ہو گیا۔'))));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${lang.t('Save failed', 'محفوظ کرنا ناکام')}: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    final bylawsPass = _bylawsReport?['passed'] == true;
    return Scaffold(
      backgroundColor: const Color(0xFFF1F5F9),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0284C7),
        title: Text(lang.t('NAKSHAI - Floor Plan', 'نقشہ اے آئی - فلور پلان'), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white)),
        actions: [
          Container(margin: const EdgeInsets.symmetric(vertical: 10, horizontal: 8), decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(8)), child: Row(children: [_buildViewToggle('2D', 0), _buildViewToggle('3D', 1)])),
          PopupMenuButton<String>(
            tooltip: lang.t('Export concept drawing', 'تصوراتی نقشہ ایکسپورٹ کریں'),
            icon: const Icon(Icons.download, color: Colors.white, size: 18),
            onSelected: _exportPlan,
            itemBuilder: (_) => [
              PopupMenuItem(value: 'pdf', child: Text(lang.t('Export PDF', 'پی ڈی ایف ایکسپورٹ'))),
              PopupMenuItem(value: 'dxf', child: Text(lang.t('Export DXF', 'ڈی ایکس ایف ایکسپورٹ'))),
            ],
          ),
          IconButton(icon: const Icon(Icons.save, color: Colors.white, size: 18), onPressed: _saveProject),
        ],
      ),
      body: Column(children: [
        if (_status.isNotEmpty) Container(width: double.infinity, padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8), color: Colors.white, child: Text(_status, style: const TextStyle(fontSize: 11, color: Color(0xFF334155)))),
        if (_selectedViewIndex == 1)
          Expanded(child: Container(margin: const EdgeInsets.all(12), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))), child: Center(child: Padding(padding: const EdgeInsets.all(20), child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.view_in_ar, size: 56, color: Color(0xFF0284C7)),
            const SizedBox(height: 12),
            Text(lang.t('3D Viewer (Beta)', 'تھری ڈی ویور (بیٹا)'), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(lang.t('Open an interactive isometric concept preview. Rotate, pan, zoom, and switch floors inside the viewer.', 'انٹرایکٹو آئیسومیٹرک تصوراتی پیش نظارہ کھولیں۔ ویور میں گھمائیں، پین کریں، زوم کریں اور منزلیں تبدیل کریں۔'), textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, color: Color(0xFF475569))),
            const SizedBox(height: 16),
            ElevatedButton.icon(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => Viewer3DScreen(plan: _currentPlanMap()))), icon: const Icon(Icons.open_in_new), label: Text(lang.t('Open 3D Viewer', 'تھری ڈی ویور کھولیں'))),
          ])))))
        else Expanded(child: Row(children: [
          Container(width: 56, color: Colors.white, child: Column(children: [
            IconButton(icon: const Icon(Icons.auto_awesome, color: Colors.purple, size: 22), tooltip: lang.t('AI Generate', 'اے آئی جنریٹ'), onPressed: _isGenerating ? null : () => _showAIGenerateDialog()),
            IconButton(icon: const Icon(Icons.view_module, color: Colors.blue, size: 22), tooltip: lang.t('3 Variants', '3 ورژن'), onPressed: _isGenerating ? null : () => _generatePlan(variants: true)),
            IconButton(icon: const Icon(Icons.home_work, color: Colors.grey, size: 22), tooltip: lang.t('Building Type', 'عمارت کی قسم'), onPressed: _showBuildingTypeDialog),
            IconButton(icon: const Icon(Icons.stairs, color: Colors.grey, size: 22), tooltip: lang.t('Floors', 'منزلیں'), onPressed: _showFloorsDialog),
            IconButton(icon: const Icon(Icons.gavel, color: Colors.grey, size: 22), tooltip: lang.t('Bylaws Pack', 'بلدیاتی پیک'), onPressed: _showBylawsDialog),
            IconButton(icon: const Icon(Icons.calculate, color: Colors.teal, size: 22), tooltip: lang.t('Material Estimate (Concept)', 'میٹیریل تخمینہ (تصور)'), onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MaterialEstimateScreen(estimate: _materialEstimate)))),
            if (_isGenerating) const Padding(padding: EdgeInsets.all(8), child: SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))),
            const Spacer(),
            if (_bylawsReport != null) Padding(padding: const EdgeInsets.only(bottom: 8), child: Icon(bylawsPass ? Icons.verified : Icons.warning_amber, color: bylawsPass ? Colors.green : Colors.orange, size: 20)),
          ])),
          Expanded(child: InteractiveViewer(minScale: 0.5, maxScale: 3.0, boundaryMargin: const EdgeInsets.all(50), child: Center(child: Container(width: 500, height: 600, margin: const EdgeInsets.all(16), child: CustomPaint(painter: FloorPlanPainter(plot: _plot, rooms: _rooms)))))),
          if (_variants.isNotEmpty) SizedBox(width: 170, child: Container(color: Colors.white, child: ListView(padding: const EdgeInsets.all(8), children: [Text(lang.t('Variants', 'ورژن'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)), const SizedBox(height: 6), ..._variants.asMap().entries.map((e) => InkWell(onTap: ()=>setState(()=>_applyPlan(e.value)), child: Container(margin: const EdgeInsets.only(bottom: 6), padding: const EdgeInsets.all(8), decoration: BoxDecoration(border: Border.all(color: const Color(0xFFE2E8F0)), borderRadius: BorderRadius.circular(8)), child: Text(e.value['title']?.toString() ?? '${lang.t('Option', 'آپشن')} ${String.fromCharCode(65+e.key)}', style: const TextStyle(fontSize: 11)))))])))
        ])),
      ]),
    );
  }

  void _showAIGenerateDialog() {
    final lang = LanguageScope.of(context);
    final c = TextEditingController(text: _prompt);
    showDialog(context: context, builder: (context) => AlertDialog(title: Text(lang.t('AI Generate Floor Plan', 'اے آئی سے فلور پلان بنائیں')), content: TextField(controller: c, maxLines: 3, decoration: InputDecoration(labelText: lang.t('Requirement', 'ضرورت'), border: const OutlineInputBorder())), actions: [TextButton(onPressed: ()=>Navigator.pop(context), child: Text(lang.t('Cancel', 'منسوخ'))), ElevatedButton(onPressed: (){ _prompt=c.text; Navigator.pop(context); _generatePlan(); }, child: Text(lang.t('Generate', 'بنائیں')))]));
  }
  void _showBuildingTypeDialog() { final lang = LanguageScope.of(context); showDialog(context: context, builder: (context) => SimpleDialog(title: Text(lang.t('Building Type', 'عمارت کی قسم')), children: ['house','plaza','shop','warehouse','duplex'].map((t)=>SimpleDialogOption(onPressed: (){ setState(()=>_buildingType=t); Navigator.pop(context); }, child: Text(t))).toList())); }
  void _showFloorsDialog() { final lang = LanguageScope.of(context); showDialog(context: context, builder: (context) => SimpleDialog(title: Text(lang.t('Floors', 'منزلیں')), children: [1,2,3].map((f)=>SimpleDialogOption(onPressed: (){ setState(()=>_floors=f); Navigator.pop(context); }, child: Text(f==1?lang.t('Ground', 'گراؤنڈ'):'G+${f-1}'))).toList())); }
  void _showBylawsDialog() { final lang = LanguageScope.of(context); showDialog(context: context, builder: (context) => SimpleDialog(title: Text(lang.t('Bylaws Pack (Concept)', 'بلدیاتی پیک (تصور)')), children: ['pakistan_generic','dha_lahore','lda_lahore','cda_islamabad','sbca_karachi'].map((p)=>SimpleDialogOption(onPressed: (){ setState(()=>_bylawsPack=p); Navigator.pop(context); }, child: Text(p))).toList())); }
  Widget _buildViewToggle(String label, int index) { final isSelected = _selectedViewIndex == index; return GestureDetector(onTap: ()=>setState(()=>_selectedViewIndex=index), child: Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4), decoration: BoxDecoration(color: isSelected ? Colors.white : Colors.transparent, borderRadius: BorderRadius.circular(6)), child: Text(label, style: TextStyle(color: isSelected ? const Color(0xFF0284C7):Colors.white, fontWeight: FontWeight.bold, fontSize: 11)))); }
}
