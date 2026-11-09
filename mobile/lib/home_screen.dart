import 'package:flutter/material.dart';
import 'screens/floor_plan_editor_screen.dart';
import 'projects_screen.dart';
import 'ai_advisor_screen.dart';
import 'profile_screen.dart';
import 'material_estimate_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(width: 48, height: 48, decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)]), borderRadius: BorderRadius.circular(12)), child: const Icon(Icons.home_work, color: Colors.white, size: 26)),
                  const SizedBox(width: 12),
                  const Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text('NAKSHAI', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2)), Text('AI Architecture SaaS (Concept)', style: TextStyle(fontSize: 12, color: Color(0xFF64748B)))])),
                  IconButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())), icon: const Icon(Icons.person_outline), style: IconButton.styleFrom(backgroundColor: Colors.white)),
                ],
              ),
              const SizedBox(height: 10),
              Container(padding: const EdgeInsets.all(10), decoration: BoxDecoration(color: const Color(0xFFFFF7ED), border: Border.all(color: const Color(0xFFFED7AA)), borderRadius: BorderRadius.circular(10)), child: const Text('Concept tool only. Exports are concept drawings — verify bylaws, structure, MEP, and costs with licensed professionals before construction/submission.', style: TextStyle(fontSize: 11, color: Color(0xFF9A3412)))),
              const SizedBox(height: 32),
              const Text('Create Your Dream Home', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
              const SizedBox(height: 6),
              const Text('Generate AI-powered floor plans in seconds', style: TextStyle(fontSize: 14, color: Color(0xFF64748B))),
              const SizedBox(height: 24),
              GestureDetector(
                onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FloorPlanEditorScreen())),
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)]),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: const [BoxShadow(color: Color(0x402563EB), blurRadius: 20, offset: Offset(0, 10))],
                  ),
                  child: Row(
                    children: [
                      Container(
                        width: 56,
                        height: 56,
                        decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.2), borderRadius: BorderRadius.circular(12)),
                        child: const Icon(Icons.add_home_work, color: Colors.white, size: 28),
                      ),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('New Floor Plan', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                            SizedBox(height: 4),
                            Text('Start from scratch with AI', style: TextStyle(color: Colors.white70, fontSize: 13)),
                          ],
                        ),
                      ),
                      const Icon(Icons.arrow_forward_ios, color: Colors.white, size: 18),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: _buildCard(context, Icons.auto_awesome, 'AI Advisor', 'Get layout suggestions', const Color(0xFF7C3AED), () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AIAdvisorScreen()))),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildCard(context, Icons.folder_open, 'My Projects', 'View saved plans', const Color(0xFF059669), () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProjectsScreen()))),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: _buildCard(context, Icons.view_in_ar, '3D Preview', 'Realistic walkthrough', const Color(0xFFEA580C), () => Navigator.push(context, MaterialPageRoute(builder: (_) => const FloorPlanEditorScreen()))),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _buildCard(context, Icons.calculate, 'Material Estimate', 'BOQ & Cost', const Color(0xFF0891B2), () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MaterialEstimateScreen()))),
                  ),
                ],
              ),
              const SizedBox(height: 32),
              const Text('Quick Features', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF0F172A))),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
                child: Column(
                  children: [
                    _buildFeatureRow(Icons.architecture, '2D & 3D Views'),
                    _buildFeatureRow(Icons.description, 'PDF & DXF Export'),
                    _buildFeatureRow(Icons.payments, 'Credits & Payments'),
                    _buildFeatureRow(Icons.security, 'Pakistani Bylaws'),
                  ],
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCard(BuildContext context, IconData icon, String title, String subtitle, Color color, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
            const SizedBox(height: 2),
            Text(subtitle, style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
          ],
        ),
      ),
    );
  }

  Widget _buildFeatureRow(IconData icon, String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFF2563EB)),
          const SizedBox(width: 10),
          Text(text, style: const TextStyle(fontSize: 13, color: Color(0xFF475569))),
        ],
      ),
    );
  }
}
