import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'services/language_service.dart';

class AIAdvisorScreen extends StatefulWidget {
  const AIAdvisorScreen({super.key});
  @override
  State<AIAdvisorScreen> createState() => _AIAdvisorScreenState();
}

class _AIAdvisorScreenState extends State<AIAdvisorScreen> {
  final widthController = TextEditingController(text: '25');
  final lengthController = TextEditingController(text: '45');
  String buildingType = 'house';
  int floors = 1;
  bool loading = false;
  List suggestions = [];

  Future<void> getSuggestions() async {
    final lang = LanguageScope.of(context);
    setState(() => loading = true);
    try {
      final data = await ApiService.post('/plans/suggest', {
        'plot_width': double.tryParse(widthController.text) ?? 25,
        'plot_length': double.tryParse(lengthController.text) ?? 45,
        'building_type': buildingType,
        'floors': floors,
      });
      setState(() => suggestions = (data['suggestions'] as List?) ?? []);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${lang.t('Error', 'خرابی')}: $e')));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(backgroundColor: Colors.white, elevation: 0, title: Text(lang.t('AI Layout Advisor', 'اے آئی لے آؤٹ مشیر'), style: const TextStyle(color: Color(0xFF0F172A)))),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(child: TextField(controller: widthController, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: lang.t('Width (ft)', 'چوڑائی (فٹ)'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(10))))),
                      const SizedBox(width: 12),
                      Expanded(child: TextField(controller: lengthController, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: lang.t('Length (ft)', 'لمبائی (فٹ)'), border: OutlineInputBorder(borderRadius: BorderRadius.circular(10))))),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Wrap(spacing: 8, children: ['house', 'plaza', 'shop', 'warehouse', 'duplex'].map((type) => ChoiceChip(label: Text(type.toUpperCase()), selected: buildingType == type, onSelected: (_) => setState(() => buildingType = type))).toList()),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: loading ? null : getSuggestions,
                      icon: loading ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.auto_awesome),
                      label: Text(loading ? lang.t('Analyzing...', 'تجزیہ ہو رہا ہے...') : lang.t('Get AI Suggestions', 'اے آئی تجاویز حاصل کریں')),
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF7C3AED), padding: const EdgeInsets.symmetric(vertical: 12)),
                    ),
                  )
                ],
              ),
            ),
            if (suggestions.isNotEmpty) ...[
              const SizedBox(height: 16),
              ...suggestions.map((s) => Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text((s['title'] ?? '').toString(), style: const TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 4),
                        Text((s['description'] ?? '').toString(), style: const TextStyle(color: Color(0xFF64748B), fontSize: 13)),
                      ],
                    ),
                  ))
            ]
          ],
        ),
      ),
    );
  }
}
