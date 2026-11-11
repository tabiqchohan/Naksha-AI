import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://naksha-ai-usaz.onrender.com/api/v1',
  );

  static Future<String?> token() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('token') ?? prefs.getString('nakshai_token');
  }

  static Future<String?> getToken() => token();

  static Future<bool> isLoggedIn() async {
    final t = await token();
    return t != null && t.isNotEmpty;
  }

  static Future<Map<String, dynamic>?> getUser() => currentUser();

  static Future<Map<String, dynamic>?> getMe() async {
    final data = await get('/auth/me', auth: true);
    return data is Map ? Map<String, dynamic>.from(data) : null;
  }

  static Future<Map<String, dynamic>> login(String username, String password) async {
    final res = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': username, 'password': password},
    );
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    final data = _decode(res);
    final map = Map<String, dynamic>.from(data as Map);
    final user = map['user'] is Map ? Map<String, dynamic>.from(map['user'] as Map) : <String, dynamic>{};
    await saveSession(map['access_token']?.toString() ?? '', user);
    return map;
  }

  static Future<dynamic> register({required String username, required String email, required String password, String? fullName}) async {
    return post('/auth/register', {
      'username': username,
      'email': email,
      'password': password,
      'full_name': fullName ?? username,
    });
  }

  static Future<dynamic> requestPasswordReset(String email) {
    return post('/auth/password-reset/request', {'email': email});
  }

  static Future<dynamic> confirmPasswordReset(String resetToken, String newPassword) {
    return post('/auth/password-reset/confirm', {'token': resetToken, 'new_password': newPassword});
  }

  static Future<dynamic> requestEmailVerification() {
    return post('/auth/email-verification/request', {}, auth: true);
  }

  static Future<dynamic> confirmEmailVerification(String verificationToken) {
    return post('/auth/email-verification/confirm', {'token': verificationToken});
  }

  static Future<Map<String, String>> headers({bool json = true, bool auth = false}) async {
    final h = <String, String>{};
    if (json) h['Content-Type'] = 'application/json';
    if (auth) {
      final t = await token();
      if (t != null && t.isNotEmpty) h['Authorization'] = 'Bearer $t';
    }
    return h;
  }

  static dynamic _decode(http.Response res) {
    if (res.body.isEmpty) return null;
    try { return jsonDecode(res.body); } catch (_) { return res.body; }
  }

  static Exception _error(http.Response res) {
    final data = _decode(res);
    final msg = data is Map ? (data['detail'] ?? data['message'] ?? 'Request failed (${res.statusCode})') : 'Request failed (${res.statusCode})';
    return Exception(msg.toString());
  }

  static Future<dynamic> get(String path, {bool auth = false}) async {
    final res = await http.get(Uri.parse('$baseUrl$path'), headers: await headers(json: false, auth: auth));
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return _decode(res);
  }

  static Future<dynamic> post(String path, dynamic body, {bool auth = false}) async {
    final res = await http.post(Uri.parse('$baseUrl$path'), headers: await headers(auth: auth), body: jsonEncode(body));
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return _decode(res);
  }

  static Future<List<int>> postBytes(String path, dynamic body, {bool auth = false}) async {
    final res = await http.post(Uri.parse('$baseUrl$path'), headers: await headers(auth: auth), body: jsonEncode(body));
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return res.bodyBytes;
  }

  static Future<dynamic> delete(String path, {bool auth = true}) async {
    final res = await http.delete(Uri.parse('$baseUrl$path'), headers: await headers(json: false, auth: auth));
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return _decode(res);
  }

  static Future<void> saveSession(String token, Map<String, dynamic> user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('token', token);
    await prefs.setString('user', jsonEncode(user));
  }

  static Future<Map<String, dynamic>?> currentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('user');
    if (raw == null) return null;
    try { return Map<String, dynamic>.from(jsonDecode(raw)); } catch (_) { return null; }
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('nakshai_token');
    await prefs.remove('user');
    await prefs.remove('nakshai_user');
  }
}
