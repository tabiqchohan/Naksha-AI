import 'package:flutter/material.dart';
import 'services/api_service.dart';
import 'services/language_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool isLogin = true;
  bool obscurePassword = true;
  bool loading = false;
  final usernameController = TextEditingController();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final fullNameController = TextEditingController();

  Future<void> handleAuth() async {
    final lang = LanguageScope.of(context);
    setState(() => loading = true);
    try {
      if (isLogin) {
        await ApiService.login(usernameController.text.trim(), passwordController.text);
        if (mounted) Navigator.pop(context, true);
      } else {
        await ApiService.register(
          username: usernameController.text.trim(),
          email: emailController.text.trim(),
          password: passwordController.text,
          fullName: fullNameController.text.trim(),
        );
        if (mounted) {
          setState(() => isLogin = true);
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.t('Registration successful. Please sign in.', 'رجسٹریشن کامیاب۔ براہ کرم سائن ان کریں۔'))));
        }
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> _showForgotPasswordDialog() async {
    final lang = LanguageScope.of(context);
    final controller = TextEditingController(text: emailController.text.trim());
    final email = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(lang.t('Reset password', 'پاس ورڈ ری سیٹ کریں')),
        content: TextField(
          controller: controller,
          keyboardType: TextInputType.emailAddress,
          decoration: InputDecoration(labelText: lang.t('Email', 'ای میل'), border: const OutlineInputBorder()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: Text(lang.t('Cancel', 'منسوخ'))),
          ElevatedButton(onPressed: () => Navigator.pop(dialogContext, controller.text.trim()), child: Text(lang.t('Send', 'بھیجیں'))),
        ],
      ),
    );
    if (email == null || email.isEmpty || !mounted) return;

    try {
      final data = await ApiService.requestPasswordReset(email);
      if (!mounted) return;
      final token = data is Map ? data['token']?.toString() : null;
      if (token != null && token.isNotEmpty) {
        await _showResetConfirmDialog(token);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.t(
          'If this email is registered, a reset link has been sent.',
          'اگر یہ ای میل رجسٹرڈ ہے تو ری سیٹ لنک بھیج دیا گیا ہے۔',
        ))));
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _showResetConfirmDialog(String token) async {
    final lang = LanguageScope.of(context);
    final controller = TextEditingController();
    final newPassword = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(lang.t('New password', 'نیا پاس ورڈ')),
        content: TextField(
          controller: controller,
          obscureText: true,
          decoration: InputDecoration(labelText: lang.t('New password (8+ characters)', 'نیا پاس ورڈ (8 یا زیادہ حروف)'), border: const OutlineInputBorder()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: Text(lang.t('Cancel', 'منسوخ'))),
          ElevatedButton(onPressed: () => Navigator.pop(dialogContext, controller.text), child: Text(lang.t('Save', 'محفوظ کریں'))),
        ],
      ),
    );
    if (newPassword == null || newPassword.isEmpty || !mounted) return;
    try {
      await ApiService.confirmPasswordReset(token, newPassword);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(lang.t('Password updated. Please sign in.', 'پاس ورڈ تبدیل ہو گیا۔ براہ کرم سائن ان کریں۔'))));
      }
    } catch (e) {
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
        title: Text(lang.t('Account', 'اکاؤنٹ'), style: const TextStyle(color: Color(0xFF0F172A))),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const SizedBox(height: 20),
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [Color(0xFF2563EB), Color(0xFF1D4ED8)]),
                borderRadius: BorderRadius.circular(20),
              ),
              child: const Icon(Icons.home_work, color: Colors.white, size: 40),
            ),
            const SizedBox(height: 16),
            const Text('NAKSHAI', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 3)),
            const SizedBox(height: 6),
            Text(isLogin ? lang.t('Sign in to continue', 'جاری رکھنے کے لیے سائن ان کریں') : lang.t('Create your account', 'اپنا اکاؤنٹ بنائیں'), style: const TextStyle(color: Color(0xFF64748B))),
            const SizedBox(height: 32),
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: const Color(0xFFE2E8F0)),
                boxShadow: const [BoxShadow(color: Color(0x0F000000), blurRadius: 10, offset: Offset(0, 4))],
              ),
              child: Column(
                children: [
                  if (!isLogin) ...[
                    TextField(
                      controller: fullNameController,
                      decoration: InputDecoration(
                        labelText: lang.t('Full Name', 'پورا نام'),
                        prefixIcon: const Icon(Icons.person_outline),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: InputDecoration(
                        labelText: lang.t('Email', 'ای میل'),
                        prefixIcon: const Icon(Icons.email_outlined),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  TextField(
                    controller: usernameController,
                    decoration: InputDecoration(
                      labelText: lang.t('Username or Email', 'صارف نام یا ای میل'),
                      prefixIcon: const Icon(Icons.account_circle_outlined),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: passwordController,
                    obscureText: obscurePassword,
                    decoration: InputDecoration(
                      labelText: lang.t('Password', 'پاس ورڈ'),
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(obscurePassword ? Icons.visibility_off : Icons.visibility),
                        onPressed: () => setState(() => obscurePassword = !obscurePassword),
                      ),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  if (isLogin) Align(
                    alignment: Alignment.centerRight,
                    child: TextButton(
                      onPressed: loading ? null : _showForgotPasswordDialog,
                      child: Text(lang.t('Forgot password?', 'پاس ورڈ بھول گئے؟')),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      onPressed: loading ? null : handleAuth,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF2563EB),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                      child: loading
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : Text(isLogin ? lang.t('Sign In', 'سائن ان') : lang.t('Create Account', 'اکاؤنٹ بنائیں'), style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () => setState(() => isLogin = !isLogin),
                    child: Text(isLogin
                        ? lang.t("Don't have an account? Sign Up", 'اکاؤنٹ نہیں ہے؟ سائن اپ کریں')
                        : lang.t('Already have an account? Sign In', 'پہلے سے اکاؤنٹ ہے؟ سائن ان کریں')),
                  )
                ],
              ),
            ),
            if (!isLogin) ...[
              const SizedBox(height: 16),
              Text(lang.t('Get 3 free credits on registration!', 'رجسٹریشن پر 3 مفت کریڈٹس حاصل کریں!'), textAlign: TextAlign.center, style: const TextStyle(color: Color(0xFF059669), fontWeight: FontWeight.w600)),
            ]
          ],
        ),
      ),
    );
  }
}
