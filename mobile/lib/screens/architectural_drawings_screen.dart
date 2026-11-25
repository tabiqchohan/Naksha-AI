import 'dart:io';
import 'package:flutter/material.dart';
import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';
import '../services/api_service.dart';
import '../services/language_service.dart';

class ArchitecturalDrawingsScreen extends StatefulWidget {
  final Map<String, dynamic> plan;
  const ArchitecturalDrawingsScreen({super.key, required this.plan});

  @override
  State<ArchitecturalDrawingsScreen> createState() => _ArchitecturalDrawingsScreenState();
}

class _ArchitecturalDrawingsScreenState extends State<ArchitecturalDrawingsScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = true;
  String _status = '';
  Map<String, dynamic>? _drawingsData;
  bool _isExportingPdf = false;
  bool _isExportingDxf = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
    _fetchDrawings();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _fetchDrawings() async {
    final lang = LanguageScope.of(context);
    setState(() {
      _isLoading = true;
      _status = lang.t('Generating architectural drawing sheets (A-01 to A-04)...', 'تعمیراتی نقشے کی شیٹس (A-01 تا A-04) بنائی جا رہی ہیں...');
    });
    try {
      final res = await ApiService.cbmDrawings(widget.plan);
      if (res is Map) {
        setState(() {
          _drawingsData = Map<String, dynamic>.from(res['drawings'] ?? res);
          _isLoading = false;
          _status = lang.t('Drawings generated successfully.', 'نقشے کامیابی سے بن گئے۔');
        });
      } else {
        throw Exception('Invalid response format');
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _status = '${lang.t('Failed to load drawings', 'نقشے لوڈ کرنے میں ناکامی')}: $e';
      });
    }
  }

  Future<void> _exportPdf() async {
    final lang = LanguageScope.of(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _isExportingPdf = true);
    try {
      final bytes = await ApiService.cbmExportPdf(widget.plan);
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}${Platform.pathSeparator}nakshai_architectural_${DateTime.now().millisecondsSinceEpoch}.pdf');
      await file.writeAsBytes(bytes, flush: true);
      await OpenFilex.open(file.path);
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('${lang.t('PDF Exported', 'پی ڈی ایف ایکسپورٹ ہو گیا')}: ${file.path}')));
    } catch (e) {
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('${lang.t('PDF Export failed', 'پی ڈی ایف ایکسپورٹ ناکام')}: $e')));
    } finally {
      if (mounted) setState(() => _isExportingPdf = false);
    }
  }

  Future<void> _exportDxf() async {
    final lang = LanguageScope.of(context);
    final messenger = ScaffoldMessenger.of(context);
    setState(() => _isExportingDxf = true);
    try {
      final bytes = await ApiService.cbmExportDxf(widget.plan);
      final dir = await getTemporaryDirectory();
      final file = File('${dir.path}${Platform.pathSeparator}nakshai_architectural_${DateTime.now().millisecondsSinceEpoch}.dxf');
      await file.writeAsBytes(bytes, flush: true);
      await OpenFilex.open(file.path);
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('${lang.t('DXF Exported', 'ڈی ایکس ایف ایکسپورٹ ہو گیا')}: ${file.path}')));
    } catch (e) {
      if (mounted) messenger.showSnackBar(SnackBar(content: Text('${lang.t('DXF Export failed', 'ڈی ایکس ایف ایکسپورٹ ناکام')}: $e')));
    } finally {
      if (mounted) setState(() => _isExportingDxf = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0284C7),
        title: Text(lang.t('Professional Architectural Drawings', 'پروفیشنل تعمیراتی نقشے'), style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white)),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          tabs: [
            Tab(text: lang.t('A-01 Floor Plan', 'A-01 فلور پلان')),
            Tab(text: lang.t('A-02 Elevations', 'A-02 ایلیویشنز')),
            Tab(text: lang.t('A-03 Sections', 'A-03 سیکشنز')),
            Tab(text: lang.t('A-04 Schedules', 'A-04 شیڈولز')),
          ],
        ),
        actions: [
          IconButton(
            icon: _isExportingPdf
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.picture_as_pdf, color: Colors.white),
            tooltip: lang.t('Export PDF Blueprint', 'پی ڈی ایف بلو پرنٹ ایکسپورٹ کریں'),
            onPressed: _isExportingPdf ? null : _exportPdf,
          ),
          IconButton(
            icon: _isExportingDxf
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.architecture, color: Colors.white),
            tooltip: lang.t('Export DXF CAD File', 'ڈی ایکس ایف سی اے ڈی فائل ایکسپورٹ کریں'),
            onPressed: _isExportingDxf ? null : _exportDxf,
          ),
        ],
      ),
      body: Column(
        children: [
          if (_status.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              color: const Color(0xFFF8FAFC),
              child: Text(_status, style: const TextStyle(fontSize: 11, color: Color(0xFF334155))),
            ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _drawingsData == null
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(lang.t('No drawing data available.', 'نقشے کا کوئی ڈیٹا دستیاب نہیں ہے۔')),
                            const SizedBox(height: 12),
                            ElevatedButton(onPressed: _fetchDrawings, child: Text(lang.t('Retry', 'دوبارہ کوشش کریں'))),
                          ],
                        ),
                      )
                    : TabBarView(
                        controller: _tabController,
                        children: [
                          _buildSheetA01FloorPlan(lang),
                          _buildSheetA02Elevations(lang),
                          _buildSheetA03Sections(lang),
                          _buildSheetA04Schedules(lang),
                        ],
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildSheetA01FloorPlan(LanguageService lang) {
    final levels = _drawingsData?['levels'] as List? ?? [];
    final site = _drawingsData?['site'] as Map? ?? {};
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lang.t('Sheet A-01: Architectural Floor Plan', 'شیڈول A-01: تعمیراتی فلور پلان'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0284C7))),
                const Divider(height: 20),
                Text('${lang.t('Plot Dimensions', 'پلاট کے سائز')}: ${site['plot_width'] ?? 0} x ${site['plot_length'] ?? 0} ft'),
                Text('${lang.t('Total Plot Area', 'کل رقبہ')}: ${site['total_area_sqft'] ?? 0} sq.ft (${site['marla_size'] ?? 0} Marla)'),
              ],
            ),
          ),
        ),
        const SizedBox(height: 12),
        ...levels.map((lvl) {
          final l = Map<String, dynamic>.from(lvl as Map);
          final rooms = l['rooms'] as List? ?? [];
          final walls = l['walls'] as List? ?? [];
          return Card(
            elevation: 1,
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${l['name'] ?? 'Level'} (Elevation: ${l['elevation'] ?? 0} ft, Height: ${l['height'] ?? 0} ft)', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  const SizedBox(height: 8),
                  Text('${lang.t('Floor Area', 'منزل کا رقبہ')}: ${l['total_area_sqft'] ?? 0} sq.ft | ${lang.t('Walls', 'دیواریں')}: ${walls.length} | ${lang.t('Rooms', 'کمرے')}: ${rooms.length}', style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
                  const Divider(height: 16),
                  ...rooms.map((r) {
                    final rm = Map<String, dynamic>.from(r as Map);
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('${rm['name']} (${rm['room_type']})', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500)),
                          Text('${rm['area_sqft']} sq.ft', style: const TextStyle(fontSize: 12, color: Color(0xFF0284C7), fontWeight: FontWeight.bold)),
                        ],
                      ),
                    );
                  }),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildSheetA02Elevations(LanguageService lang) {
    final elevations = _drawingsData?['elevations'] as Map? ?? {};
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lang.t('Sheet A-02: Orthographic Elevations', 'شیٹ A-02: آرتھوگرافک ایلیویشنز'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0284C7))),
                const Divider(height: 20),
                Text(lang.t('True orthographic projections computed from exterior walls and facade openings.', 'بیرونی دیوارों और اوپننگز سے حساب کردہ حقیقی آرتھوگرافک پروجیکشنز۔'), style: const TextStyle(fontSize: 12, color: Color(0xFF475569))),
                const SizedBox(height: 12),
                Text('${lang.t('Elevation Views', 'نماز کے مناظر')}: Front, Rear, Left, Right', style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 12)),
                const SizedBox(height: 6),
                Text('${lang.t('Total Elements Projected', 'کل پروجیکٹڈ ایلیمنٹس')}: ${elevations.length}', style: const TextStyle(fontSize: 12, color: Color(0xFF334155))),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSheetA03Sections(LanguageService lang) {
    final sections = _drawingsData?['sections'] as List? ?? [];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lang.t('Sheet A-03: Building Cross Sections', 'شیٹ A-03: بلڈنگ کراس سیکشنز'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0284C7))),
                const Divider(height: 20),
                Text(lang.t('Longitudinal and transverse sectional cuts displaying foundation, slab thickness, and floor heights.', 'بنیاد، سلیب کی موٹائی اور منزل کی اونچائی کو ظاہر کرنے والے طول البلد اور عرض البلد سیکشنل کٹس۔'), style: const TextStyle(fontSize: 12, color: Color(0xFF475569))),
                const SizedBox(height: 12),
                Text('${lang.t('Computed Sections', 'حساب شدہ سیکشنز')}: ${sections.length}', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSheetA04Schedules(LanguageService lang) {
    final schedules = _drawingsData?['schedules'] as Map? ?? {};
    final doors = schedules['doors'] as List? ?? [];
    final windows = schedules['windows'] as List? ?? [];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          elevation: 2,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lang.t('Sheet A-04: Door & Window Schedules', 'شیٹ A-04: دروازوں اور کھڑکیوں کے شیڈول'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: Color(0xFF0284C7))),
                const Divider(height: 20),
                Text('${lang.t('Total Building Area', 'کل عمارت کا رقبہ')}: ${schedules['total_building_area_sqft'] ?? 0} sq.ft', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                const SizedBox(height: 12),
                Text('${lang.t('Doors Schedule', 'دروازوں کا شیڈول')} (${doors.length})', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF0284C7))),
                ...doors.map((d) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Text('• ID: ${d['id']} | Width: ${d['width']} ft | Height: ${d['height']} ft', style: const TextStyle(fontSize: 11)),
                )),
                const SizedBox(height: 12),
                Text('${lang.t('Windows Schedule', 'کھڑکیوں کا شیڈول')} (${windows.length})', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Color(0xFF0284C7))),
                ...windows.map((w) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Text('• ID: ${w['id']} | Width: ${w['width']} ft | Height: ${w['height']} ft | Sill: ${w['sill_height']} ft', style: const TextStyle(fontSize: 11)),
                )),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
