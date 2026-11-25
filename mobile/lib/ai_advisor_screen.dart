import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'services/language_service.dart';
import 'screens/floor_plan_editor_screen.dart';
import 'login_screen.dart';

class AIAdvisorScreen extends StatefulWidget {
  const AIAdvisorScreen({super.key});
  @override
  State<AIAdvisorScreen> createState() => _AIAdvisorScreenState();
}

class _AIAdvisorScreenState extends State<AIAdvisorScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final widthController = TextEditingController(text: '30');
  final lengthController = TextEditingController(text: '60');
  final promptController = TextEditingController(text: '3 bed family home with drawing room, kitchen, and parking');
  String buildingType = 'house';
  int floors = 1;
  String bylawsPack = 'pakistan_generic';

  bool _isLoading = false;
  String _status = '';
  List _suggestions = [];
  Map<String, dynamic>? _generatedPlan;
  Map<String, dynamic>? _impactSummary;
  Map<String, dynamic>? _vastuReport;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    widthController.dispose();
    lengthController.dispose();
    promptController.dispose();
    super.dispose();
  }

  Future<bool> _ensureAuth() async {
    final lang = LanguageScope.of(context);
    final token = await ApiService.token();
    if (token != null && token.isNotEmpty) return true;
    if (!mounted) return false;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.t('Please sign in to run AI consultation & generation (credits required).', 'اے آئی مشاورت اور جنریشن کے لیے سائن ان کریں۔'))));
    await Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
    return (await ApiService.token()) != null;
  }

  Future<void> _fetchSuggestions() async {
    final lang = LanguageScope.of(context);
    setState(() {
      _isLoading = true;
      _status = lang.t('Consulting AI layout advisor...', 'اے آئی لے آؤٹ مشیر سے مشاورت جاری ہے...');
    });
    try {
      final data = await ApiService.post('/plans/suggest', {
        'plot_width': double.tryParse(widthController.text) ?? 30,
        'plot_length': double.tryParse(lengthController.text) ?? 60,
        'building_type': buildingType,
        'floors': floors,
        'style': 'modern',
      });
      setState(() {
        _suggestions = (data['suggestions'] as List?) ?? [];
        _isLoading = false;
        _status = lang.t('AI suggestions received successfully.', 'اے آئی تجاویز کامیابی سے مل گئیں۔');
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
        _status = '${lang.t('AI suggestion failed', 'اے آئی تجویز ناکام')}: $e';
      });
    }
  }

  Future<void> _generateAiPlan({bool variants = false}) async {
    final lang = LanguageScope.of(context);
    if (!await _ensureAuth()) return;
    setState(() {
      _isLoading = true;
      _status = variants ? lang.t('Generating 3 AI design variants...', '3 اے آئی ڈیزائن ورژن بنائے جا رہے ہیں...') : lang.t('Generating AI-assisted floor plan...', 'اے آئی فلور پلان بنایا جا رہا ہے...');
    });
    try {
      final base = {
        'prompt': promptController.text,
        'plot_width': double.tryParse(widthController.text) ?? 30,
        'plot_length': double.tryParse(lengthController.text) ?? 60,
        'building_type': buildingType,
        'floors': floors,
        'bedrooms': 3,
        'bathrooms': 2,
        'bylaws_pack': bylawsPack,
      };

      if (variants) {
        final res = await ApiService.post('/plans/generate-variants', {'base': base, 'count': 3}, auth: true);
        final list = (res['variants'] as List?) ?? [];
        if (list.isNotEmpty) {
          setState(() {
            _generatedPlan = Map<String, dynamic>.from(list.first as Map);
            _impactSummary = res['compare'];
            _isLoading = false;
            _status = lang.t('Generated 3 AI variants successfully.', '3 اے آئی ورژن کامیابی سے بن گئے۔');
          });
        }
      } else {
        final res = await ApiService.post('/plans/generate', base, auth: true);
        setState(() {
          _generatedPlan = Map<String, dynamic>.from(res as Map);
          _impactSummary = _generatedPlan?['impact_summary'] is Map ? Map<String, dynamic>.from(_generatedPlan!['impact_summary']) : null;
          _vastuReport = _generatedPlan?['vastu_report'] is Map ? Map<String, dynamic>.from(_generatedPlan!['vastu_report']) : null;
          _isLoading = false;
          _status = lang.t('AI floor plan generated & validated.', 'اے آئی فلور پلان بن گیا اور تصدیق ہو گئی۔');
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
        _status = '${lang.t('AI Generation failed', 'اے آئی جنریشن ناکام')}: $e';
      });
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        iconTheme: const IconThemeData(color: Color(0xFF0F172A)),
        title: Text(lang.t('Mobile AI Hub & Advisor', 'موبائل اے آئی ہب اور مشیر'), style: const TextStyle(color: Color(0xFF0F172A), fontSize: 16, fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF7C3AED),
          unselectedLabelColor: Colors.grey,
          indicatorColor: const Color(0xFF7C3AED),
          tabs: [
            Tab(text: lang.t('AI Consultation', 'اے آئی مشاورت')),
            Tab(text: lang.t('AI Generation', 'اے آئی جنریشن')),
            Tab(text: lang.t('Advisor & Vastu', 'مشیر اور واسٹو')),
          ],
        ),
      ),
      body: Column(
        children: [
          if (_status.isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              color: const Color(0xFFF1F5F9),
              child: Text(_status, style: const TextStyle(fontSize: 11, color: Color(0xFF334155))),
            ),
          Expanded(
            child: TabBarView(
              controller: _tabController,
              children: [
                _buildConsultationTab(lang),
                _buildGenerationTab(lang),
                _buildAdvisorTab(lang),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConsultationTab(LanguageService lang) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(lang.t('Plot & Building Parameters', 'پلاٹ اور عمارت کے پیرامیٹرز'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: TextField(controller: widthController, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: lang.t('Width (ft)', 'چوڑائی (فٹ)'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(10))))),
                  const SizedBox(width: 12),
                  Expanded(child: TextField(controller: lengthController, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: lang.t('Length (ft)', 'لمبائی (فٹ)'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(10))))),
                ],
              ),
              const SizedBox(height: 12),
              TextField(controller: promptController, maxLines: 2, decoration: InputDecoration(labelText: lang.t('AI Design Prompt / Requirements', 'اے آئی ڈیزائن پرامپٹ / ضروریات'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)))),
              const SizedBox(height: 12),
              Text(lang.t('Building Type', 'عمارت کی قسم'), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF64748B))),
              const SizedBox(height: 6),
              Wrap(spacing: 8, children: ['house', 'plaza', 'shop', 'warehouse', 'duplex'].map((type) => ChoiceChip(label: Text(type.toUpperCase()), selected: buildingType == type, onSelected: (_) => setState(() => buildingType = type))).toList()),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _isLoading ? null : _fetchSuggestions,
                  icon: _isLoading ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.psychology, color: Colors.white),
                  label: Text(lang.t('Get AI Layout Suggestions', 'اے آئی لے آؤٹ تجاویز حاصل کریں'), style: const TextStyle(color: Colors.white)),
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF7C3AED), padding: const EdgeInsets.symmetric(vertical: 12)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (_suggestions.isNotEmpty) ...[
          Text(lang.t('AI Layout Recommendations', 'اے آئی لے آؤٹ سفارشات'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          const SizedBox(height: 8),
          ..._suggestions.map((s) => Container(
                margin: const EdgeInsets.only(bottom: 10),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(10), border: Border.all(color: const Color(0xFFE2E8F0))),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text((s['title'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF7C3AED))),
                    const SizedBox(height: 4),
                    Text((s['description'] ?? '').toString(), style: const TextStyle(color: Color(0xFF475569), fontSize: 12)),
                  ],
                ),
              )),
        ]
      ],
    );
  }

  Widget _buildGenerationTab(LanguageService lang) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(lang.t('AI-Assisted Plan Generation & Variants', 'اے آئی معاونت سے پلان جنریشن اور ورژن'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: bylawsPack,
                decoration: InputDecoration(labelText: lang.t('Bylaws Jurisdiction', 'بلدیاتی دائرہ اختیار'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(10))),
                items: ['pakistan_generic', 'dha_lahore', 'lda_lahore', 'cda_islamabad', 'sbca_karachi'].map((p) => DropdownMenuItem(value: p, child: Text(p))).toList(),
                onChanged: (v) => setState(() => bylawsPack = v ?? 'pakistan_generic'),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : () => _generateAiPlan(variants: false),
                      icon: const Icon(Icons.auto_awesome, color: Colors.white),
                      label: Text(lang.t('Generate Plan', 'پلان بنائیں'), style: const TextStyle(color: Colors.white)),
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2563EB), padding: const EdgeInsets.symmetric(vertical: 12)),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: _isLoading ? null : () => _generateAiPlan(variants: true),
                      icon: const Icon(Icons.view_module, color: Colors.white),
                      label: Text(lang.t('Generate 3 Variants', '3 ورژن بنائیں'), style: const TextStyle(color: Colors.white)),
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF059669), padding: const EdgeInsets.symmetric(vertical: 12)),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        if (_generatedPlan != null) ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFF22C55E))),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(_generatedPlan!['title'] ?? 'Generated Concept Plan', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF15803D))),
                    ElevatedButton(
                      onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FloorPlanEditorScreen(initialPlan: _generatedPlan))),
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2563EB)),
                      child: Text(lang.t('Open in Editor', 'ایڈیٹر میں کھولیں')),
                    ),
                  ],
                ),
                const Divider(height: 20),
                Text('${lang.t('Rooms Generated', 'بنائے گئے کمرے')}: ${(_generatedPlan!['rooms'] as List? ?? []).length}'),
                Text('${lang.t('Estimated Cost', 'تخمینہ لاگت')}: PKR ${(_generatedPlan!['material_estimate']?['estimated_cost_pkr'] ?? 0)}'),
              ],
            ),
          ),
        ]
      ],
    );
  }

  Widget _buildAdvisorTab(LanguageService lang) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(lang.t('Design Advisor & Impact Assessment', 'ڈیزائن مشیر اور اثرات کا جائزہ'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              const Divider(height: 20),
              if (_impactSummary != null) ...[
                Text('${lang.t('Total Area', 'کل رقبہ')}: ${_impactSummary!['total_area_sqft']} sq.ft'),
                Text('${lang.t('Covered Area', 'ڈھکا ہوا رقبہ')}: ${_impactSummary!['covered_area_sqft']} sq.ft (${_impactSummary!['coverage_percent']}%)'),
                const SizedBox(height: 12),
                Text(lang.t('Sun & Ventilation Advice', 'دھوپ اور ہوادار بنانے کی ہدایت'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
                Text((_impactSummary!['sun_ventilation']?['cross_ventilation'] ?? '').toString(), style: const TextStyle(fontSize: 12, color: Color(0xFF475569))),
              ] else ...[
                Text(lang.t('Generate an AI plan first to view advisor heuristics and Vastu recommendations.', 'مشیر اور واسٹو سفارشات دیکھنے کے لیے پہلے اے آئی پلان بنائیں۔'), style: const TextStyle(color: Color(0xFF64748B), fontSize: 12)),
              ],
              if (_vastuReport != null) ...[
                const Divider(height: 20),
                Text('${lang.t('Vastu Advisory Score', 'واسٹو سکور')}: ${_vastuReport!['score']} / 100', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Color(0xFF7C3AED))),
                const SizedBox(height: 6),
                Text((_vastuReport!['summary'] ?? '').toString(), style: const TextStyle(fontSize: 12)),
              ],
            ],
          ),
        ),
      ],
    );
  }
}
