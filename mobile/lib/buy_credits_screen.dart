import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'services/language_service.dart';
import 'login_screen.dart';

class BuyCreditsScreen extends StatefulWidget {
  const BuyCreditsScreen({super.key});

  @override
  State<BuyCreditsScreen> createState() => _BuyCreditsScreenState();
}

class _BuyCreditsScreenState extends State<BuyCreditsScreen> {
  List plans = [];
  bool loading = true;
  String? buyingId;
  String method = 'stripe';
  String status = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await ApiService.get('/payments/pricing');
      final packs = data['packs'] as Map? ?? {};
      final list = packs.entries.map((e) => {'credits': int.parse(e.key.toString()), ...Map<String, dynamic>.from(e.value as Map)}).toList()
        ..sort((a, b) => (a['credits'] as int).compareTo(b['credits'] as int));
      setState(() {
        plans = list;
        loading = false;
      });
    } catch (e) {
      setState(() {
        loading = false;
        status = e.toString();
        plans = [
          {'credits': 10, 'pkr': 500, 'usd': 1.8, 'name': '10 Credits'},
          {'credits': 25, 'pkr': 1000, 'usd': 3.6, 'name': '25 Credits'},
          {'credits': 50, 'pkr': 1800, 'usd': 6.5, 'name': '50 Credits'},
          {'credits': 100, 'pkr': 3000, 'usd': 10.8, 'name': '100 Credits'},
        ];
      });
    }
  }

  Future<bool> _ensureAuth() async {
    final t = await ApiService.token();
    if (t != null && t.isNotEmpty) return true;
    if (!mounted) return false;
    await Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen()));
    return (await ApiService.token()) != null;
  }

  Future<void> _buy(Map p) async {
    final lang = LanguageScope.of(context);
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(lang.t('Temporarily Unavailable', 'عارضی طور پر دستیاب نہیں')),
        content: Text(lang.t('Subscriptions and credit purchases are temporarily disabled during Google Play Closed Testing.', 'گوگل پلے کلوزڈ ٹیسٹنگ کے دوران سبسکرپشنز اور کریڈٹس کی خریداری عارضی طور پر معطل ہے۔')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text(lang.t('OK', 'ٹھیک ہے'))),
        ],
      ),
    );
  }

  Future<void> _verify(String txn) async {
    final lang = LanguageScope.of(context);
    try {
      final res = await ApiService.post('/payments/verify/$txn', {}, auth: true);
      final msg = res['message']?.toString() ?? res.toString();
      if (!mounted) return;
      if (res['credits'] != null) {
        final u = await ApiService.getUser() ?? {};
        u['credits'] = res['credits'];
        await ApiService.saveSession(await ApiService.getToken() ?? '', u);
      }
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${lang.t('Verify', 'تصدیق')}: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(backgroundColor: Colors.white, elevation: 0, title: Text(lang.t('Buy Credits', 'کریڈٹس خریدیں'), style: const TextStyle(color: Color(0xFF0F172A)))),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(lang.t('Choose a Plan', 'پلان منتخب کریں'), style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 6),
                  Text(lang.t('Backend-managed credits/payments. Manual verify is gated for production gateways.', 'کریڈٹس/ادائیگیاں بیک اینڈ سے منظم۔ پروڈکشن گیٹ ویز کے لیے مینوئل تصدیق مشروط ہے۔'), style: const TextStyle(color: Color(0xFF64748B), fontSize: 12)),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    initialValue: method,
                    items: [
                      DropdownMenuItem(value: 'stripe', child: Text(lang.t('Stripe (card)', 'اسٹرائپ (کارڈ)'))),
                      DropdownMenuItem(value: 'jazzcash', child: Text(lang.t('JazzCash', 'جاز کیش'))),
                      DropdownMenuItem(value: 'easypaisa', child: Text(lang.t('Easypaisa', 'ایزی پیسہ'))),
                      DropdownMenuItem(value: 'dev', child: Text(lang.t('Dev/test record', 'ڈیو/ٹیسٹ ریکارڈ'))),
                    ],
                    onChanged: (v) => setState(() => method = v ?? 'stripe'),
                    decoration: InputDecoration(labelText: lang.t('Payment Method', 'ادائیگی کا طریقہ'), border: const OutlineInputBorder()),
                  ),
                  const SizedBox(height: 16),
                  ...plans.map((p) => Container(
                        margin: const EdgeInsets.only(bottom: 12),
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(p['name']?.toString() ?? '${p['credits']} ${lang.t('Credits', 'کریڈٹس')}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                                  Text('${p['credits']} ${lang.t('Credits', 'کریڈٹس')} · \$${p['usd']}', style: const TextStyle(color: Color(0xFF64748B))),
                                ],
                              ),
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text('Rs ${p['pkr']}', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF2563EB))),
                                const SizedBox(height: 4),
                                ElevatedButton(
                                  onPressed: buyingId == '${p['credits']}' ? null : () => _buy(Map<String, dynamic>.from(p)),
                                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF2563EB)),
                                  child: Text(buyingId == '${p['credits']}' ? '...' : lang.t('Buy', 'خریدیں')),
                                ),
                              ],
                            )
                          ],
                        ),
                      )),
                  if (status.isNotEmpty)
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
                      child: Text(status, style: const TextStyle(fontSize: 12, color: Color(0xFF475569))),
                    ),
                ],
              ),
            ),
    );
  }
}
