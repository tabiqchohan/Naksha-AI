import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

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
  final String baseUrl = 'https://naksha-ai-usaz.onrender.com/api/v1';

  Future<void> handleAuth() async {
    setState(() => loading = true);
    try {
      if (isLogin) {
        var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/auth/login'));
        request.fields['username'] = usernameController.text;
        request.fields['password'] = passwordController.text;
        var response = await request.send();
        var body = await response.stream.bytesToString();
        if (response.statusCode == 200) {
          var data = jsonDecode(body);
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('token', data['access_token']);
          await prefs.setString('user', jsonEncode(data['user']));
          if (mounted) Navigator.pop(context, true);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Login failed')));
        }
      } else {
        final res = await http.post(
          Uri.parse('$baseUrl/auth/register'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({
            'username': usernameController.text,
            'email': emailController.text,
            'password': passwordController.text,
            'full_name': fullNameController.text,
          }),
        );
        if (res.statusCode == 200) {
          setState(() => isLogin = true);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Registration successful! Please login.')));
        } else {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Registration failed')));
        }
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: const Text('Account', style: TextStyle(color: Color(0xFF0F172A))),
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
            Text(isLogin ? 'Sign in to continue' : 'Create your account', style: const TextStyle(color: Color(0xFF64748B))),
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
                        labelText: 'Full Name',
                        prefixIcon: const Icon(Icons.person_outline),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: emailController,
                      decoration: InputDecoration(
                        labelText: 'Email',
                        prefixIcon: const Icon(Icons.email_outlined),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],
                  TextField(
                    controller: usernameController,
                    decoration: InputDecoration(
                      labelText: 'Username',
                      prefixIcon: const Icon(Icons.account_circle_outlined),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: passwordController,
                    obscureText: obscurePassword,
                    decoration: InputDecoration(
                      labelText: 'Password',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(obscurePassword ? Icons.visibility_off : Icons.visibility),
                        onPressed: () => setState(() => obscurePassword = !obscurePassword),
                      ),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 24),
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
                          : Text(isLogin ? 'Sign In' : 'Create Account', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () => setState(() => isLogin = !isLogin),
                    child: Text(isLogin ? "Don't have an account? Sign Up" : "Already have an account? Sign In"),
                  )
                ],
              ),
            ),
            if (!isLogin) ...[
              const SizedBox(height: 16),
              const Text('🎉 Get 3 free credits on registration!', style: TextStyle(color: Color(0xFF059669), fontWeight: FontWeight.w600)),
            ]
          ],
        ),
      ),
    );
  }
}
