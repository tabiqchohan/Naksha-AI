import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../services/language_service.dart';
import '../login_screen.dart';

class SubscriptionWalletScreen extends StatefulWidget {
  const SubscriptionWalletScreen({super.key});

  @override
  State<SubscriptionWalletScreen> createState() => _SubscriptionWalletScreenState();
}

class _SubscriptionWalletScreenState extends State<SubscriptionWalletScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoading = true;
  String _status = '';
  Map<String, dynamic> _pricing = {};
  Map<String, dynamic> _subscriptionStatus = {};
  Map<String, dynamic>? _currentUser;
  bool _isProcessingCheckout = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _loadData();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    final lang = LanguageScope.of(context);
    setState(() {
      _isLoading = true;
      _status = lang.t('Loading subscription & credit data...', 'سبسکرپشن اور کریڈٹ کا ڈیٹا لوڈ ہو رہا ہے...');
    });
    try {
      final pricingRes = await ApiService.get('/payments/pricing');
      final subRes = await ApiService.get('/payments/subscription/status', auth: true);
      final meRes = await ApiService.getMe();

      if (!mounted) return;
      setState(() {
        _pricing = pricingRes is Map ? Map<String, dynamic>.from(pricingRes) : {};
        _subscriptionStatus = subRes is Map ? Map<String, dynamic>.from(subRes) : {};
        _currentUser = meRes is Map ? Map<String, dynamic>.from(meRes!) : null;
        _isLoading = false;
        _status = '';
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _isLoading = false;
        _status = '${lang.t('Failed to load wallet data', 'والٹ ڈیٹا لوڈ کرنے میں ناکامی')}: $e';
      });
    }
  }

  Future<void> _checkoutSubscription(String planSlug) async {
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

  @override
  Widget build(BuildContext context) {
    final lang = LanguageScope.of(context);
    final credits = _currentUser?['credits'] ?? 3;
    final planType = _currentUser?['plan_type'] ?? 'free';

    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: const Color(0xFF0284C7),
        title: Text(lang.t('Subscriptions & Credit Wallet', 'سبسکرپشن اور کریڈٹ والٹ'), style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white)),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: Colors.white,
          tabs: [
            Tab(text: lang.t('Subscription Plans', 'سبسکرپشن پلانز')),
            Tab(text: lang.t('Credit Wallet', 'کریڈٹ والٹ')),
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
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : TabBarView(
                    controller: _tabController,
                    children: [
                      _buildSubscriptionsTab(lang, planType),
                      _buildWalletTab(lang, credits),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildSubscriptionsTab(LanguageService lang, String currentPlan) {
    final subs = _pricing['subscriptions'] as Map? ?? {};
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF0284C7), Color(0xFF0369A1)]), borderRadius: BorderRadius.circular(12)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(lang.t('Current Active Plan', 'موجودہ فعال پلان'), style: const TextStyle(color: Colors.white70, fontSize: 12)),
              const SizedBox(height: 4),
              Text(currentPlan.toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              Text('${lang.t('Status', 'حالت')}: ${_subscriptionStatus['status'] ?? 'active'}', style: const TextStyle(color: Colors.white70, fontSize: 12)),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Text(lang.t('Available Subscription Tiers', 'دستیاب سبسکرپشن ٹیئرز'), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
        const SizedBox(height: 10),
        ...subs.entries.map((e) {
          final slug = e.key.toString();
          final info = Map<String, dynamic>.from(e.value as Map);
          final isCurrent = currentPlan.toLowerCase() == slug.toLowerCase();
          return Card(
            elevation: 1,
            margin: const EdgeInsets.only(bottom: 12),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(slug.toUpperCase(), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Color(0xFF0284C7))),
                      Text('\$${info['usd']} / mo (PKR ${info['pkr']})', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: Color(0xFF0F172A))),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text('${lang.t('Allocated Credits', 'مختص کریڈٹس')}: ${info['credits']} ${lang.t('credits/mo', 'کریڈٹس/ماہ')}', style: const TextStyle(fontSize: 12, color: Color(0xFF475569))),
                  const Divider(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: isCurrent || _isProcessingCheckout ? null : () => _checkoutSubscription(slug),
                      style: ElevatedButton.styleFrom(backgroundColor: isCurrent ? Colors.grey : const Color(0xFF0284C7)),
                      child: Text(isCurrent ? lang.t('Current Plan', 'موجودہ پلان') : lang.t('Subscribe', 'سبسکرائب کریں')),
                    ),
                  ),
                ],
              ),
            ),
          );
        }),
      ],
    );
  }

  Widget _buildWalletTab(LanguageService lang, dynamic credits) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: const Color(0xFFE2E8F0))),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(lang.t('Authoritative Credit Balance', 'مستند کریڈٹ بیلنس'), style: const TextStyle(color: Color(0xFF64748B), fontSize: 12)),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('$credits', style: const TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: Color(0xFF0284C7))),
                  const Icon(Icons.bolt, size: 36, color: Color(0xFF0284C7)),
                ],
              ),
              const Divider(height: 24),
              Text(lang.t('Credits are managed authoritatively on the backend ledger. Use Buy Credits for purchasing additional credit packs.', 'کریڈٹس بیک اینڈ لیجر پر مستند طریقے سے منظم ہوتے ہیں۔ اضافی کریڈٹ پیکس خریدنے کے لیے کریڈٹس خریدیں استعمال کریں۔'), style: const TextStyle(fontSize: 11, color: Color(0xFF64748B))),
            ],
          ),
        ),
      ],
    );
  }
}
