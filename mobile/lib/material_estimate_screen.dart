import 'package:flutter/material.dart';

class MaterialEstimateScreen extends StatelessWidget {
  final Map<String, dynamic>? estimate;
  const MaterialEstimateScreen({super.key, this.estimate});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text('Material Estimate', style: TextStyle(color: Color(0xFF0F172A))),
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
              child: const Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Bill of Quantities (BOQ)', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                  SizedBox(height: 4),
                  Text('Estimated cost for your floor plan', style: TextStyle(color: Colors.white70)),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _buildItem('Bricks', '${estimate?['bricks_count'] ?? 0}', 'pcs', Icons.view_module),
            _buildItem('Cement', '${estimate?['cement_bags'] ?? 0}', 'bags', Icons.inventory_2),
            _buildItem('Steel', '${estimate?['steel_tons'] ?? 0}', 'tons', Icons.settings_input_component),
            _buildItem('Sand', '${estimate?['sand_cft'] ?? 0}', 'cft', Icons.grain),
            _buildItem('Crush', '${estimate?['crush_cft'] ?? 0}', 'cft', Icons.landscape),
            const SizedBox(height: 16),
            Container(width: double.infinity, padding: const EdgeInsets.all(16), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Total Estimated Cost (Concept)', style: TextStyle(color: Color(0xFF64748B))),
              const SizedBox(height: 4),
              Text('PKR ${(estimate?['estimated_cost_pkr'] ?? 0).toString()}', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Color(0xFF059669))),
              Text('~ USD ${(estimate?['estimated_cost_usd'] ?? 0).toString()}', style: const TextStyle(color: Color(0xFF64748B))),
            ])),
            const SizedBox(height: 12),
            const Text('* Concept estimate only. Rates vary by city/material/finish. Verify with licensed professionals before construction.', style: TextStyle(fontSize: 11, color: Color(0xFF64748B))),
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
