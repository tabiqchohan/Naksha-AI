import 'package:flutter/material.dart';
import 'services/language_service.dart';

class MaterialEstimateScreen extends StatelessWidget {
  final Map<String, dynamic>? estimate;
  const MaterialEstimateScreen({super.key, this.estimate});

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(lang.t('Material Estimate', 'میٹیریل تخمینہ'), style: const TextStyle(color: Color(0xFF0F172A))),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF059669), Color(0xFF047857)]), borderRadius: BorderRadius.circular(12)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(lang.t('Bill of Quantities (BOQ)', 'بل آف کوانٹٹیز (بی او کیو)'), style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  Text(lang.t('Estimated cost for your floor plan', 'آپ کے فلور پلان کی تخمینی لاگت'), style: const TextStyle(color: Colors.white70)),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _buildItem(lang.t('Bricks', 'اینٹیں'), '${estimate?['bricks_count'] ?? 0}', lang.t('pcs', 'عدد'), Icons.view_module),
            _buildItem(lang.t('Cement', 'سیمنٹ'), '${estimate?['cement_bags'] ?? 0}', lang.t('bags', 'بورے'), Icons.inventory_2),
            _buildItem(lang.t('Steel', 'سٹیل'), '${estimate?['steel_tons'] ?? 0}', lang.t('tons', 'ٹن'), Icons.settings_input_component),
            _buildItem(lang.t('Sand', 'ریت'), '${estimate?['sand_cft'] ?? 0}', lang.t('cft', 'کیوبک فٹ'), Icons.grain),
            _buildItem(lang.t('Crush', 'کرش'), '${estimate?['crush_cft'] ?? 0}', lang.t('cft', 'کیوبک فٹ'), Icons.landscape),
            const SizedBox(height: 16),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(lang.t('Total Estimated Cost (Concept)', 'کل تخمینی لاگت (تصور)'), style: const TextStyle(color: Color(0xFF64748B))),
                  const SizedBox(height: 4),
                  Text('PKR ${(estimate?['estimated_cost_pkr'] ?? 0).toString()}', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF059669))),
                  Text('~ USD ${(estimate?['estimated_cost_usd'] ?? 0).toString()}', style: const TextStyle(color: Color(0xFF64748B))),
                ],
              ),
            ),
            const SizedBox(height: 12),
            Text(lang.t(
              '* Concept estimate only. Rates vary by city/material/finish. Verify with licensed professionals before construction.',
              '* صرف تصوراتی تخمینہ۔ شرحیں شہر/میٹیریل/فنش کے لحاظ سے مختلف ہوتی ہیں۔ تعمیر سے پہلے لائسنس یافتہ پیشہ ور افراد سے تصدیق کریں۔',
            ), style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
          ],
        ),
      ),
    );
  }

  Widget _buildItem(String name, String qty, String unit, IconData icon) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
      child: Row(
        children: [
          Container(width: 40, height: 40, decoration: BoxDecoration(color: const Color(0xFFDCFCE7), borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: const Color(0xFF059669))),
          const SizedBox(width: 12),
          Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.w600))),
          Text('$qty $unit', style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
