import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://naksha-ai-usaz.onrender.com/api/v1',
  );

  static const FlutterSecureStorage _secureStorage = FlutterSecureStorage();
  static const String _secureTokenKey = 'nakshai_secure_token';

  // Getter for token with secure storage and safe legacy SharedPreferences migration
  static Future<String?> token() async {
    try {
      final secureT = await _secureStorage.read(key: _secureTokenKey);
      if (secureT != null && secureT.isNotEmpty) {
        return secureT;
      }

      // Fallback and migrate from legacy SharedPreferences
      final prefs = await SharedPreferences.getInstance();
      final legacyT = prefs.getString('token') ?? prefs.getString('nakshai_token');
      if (legacyT != null && legacyT.isNotEmpty) {
        await _secureStorage.write(key: _secureTokenKey, value: legacyT);
        final verified = await _secureStorage.read(key: _secureTokenKey);
        if (verified == legacyT) {
          await prefs.remove('token');
          await prefs.remove('nakshai_token');
        }
        return legacyT;
      }
      return null;
    } catch (_) {
      // Fallback to legacy if secure storage throws platform error
      final prefs = await SharedPreferences.getInstance();
      return prefs.getString('token') ?? prefs.getString('nakshai_token');
    }
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
    if (res.statusCode == 401) {
      await logout();
    }
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
    if (res.statusCode == 401) {
      logout();
    }
    final data = _decode(res);
    final msg = data is Map ? (data['detail'] ?? data['message'] ?? 'Request failed (${res.statusCode})') : 'Request failed (${res.statusCode})';
    return Exception(msg.toString());
  }

  static Future<dynamic> get(String path, {bool auth = false}) async {
    final res = await http.get(Uri.parse('$baseUrl$path'), headers: await headers(json: false, auth: auth));
    if (res.statusCode == 401) {
      await logout();
    }
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return _decode(res);
  }

  static Future<dynamic> post(String path, dynamic body, {bool auth = false}) async {
    final res = await http.post(Uri.parse('$baseUrl$path'), headers: await headers(auth: auth), body: jsonEncode(body));
    if (res.statusCode == 401) {
      await logout();
    }
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return _decode(res);
  }

  static Future<List<int>> postBytes(String path, dynamic body, {bool auth = false}) async {
    final res = await http.post(Uri.parse('$baseUrl$path'), headers: await headers(auth: auth), body: jsonEncode(body));
    if (res.statusCode == 401) {
      await logout();
    }
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return res.bodyBytes;
  }

  static Future<dynamic> delete(String path, {bool auth = true}) async {
    final res = await http.delete(Uri.parse('$baseUrl$path'), headers: await headers(json: false, auth: auth));
    if (res.statusCode == 401) {
      await logout();
    }
    if (res.statusCode < 200 || res.statusCode >= 300) throw _error(res);
    return _decode(res);
  }

  // CBM API Integration Helpers
  static Future<dynamic> cbmUpdate(Map<String, dynamic> cbm) async {
    return post('/plans/cbm-update', cbm, auth: true);
  }

  static Future<dynamic> cbmBoq(Map<String, dynamic> cbm) async {
    return post('/plans/cbm-boq', cbm, auth: true);
  }

  static Future<dynamic> cbmDrawings(Map<String, dynamic> plan) async {
    return post('/plans/cbm-drawings', plan, auth: true);
  }

  static Future<List<int>> cbmExportPdf(Map<String, dynamic> plan) async {
    return postBytes('/plans/cbm-export-pdf', plan, auth: true);
  }

  static Future<List<int>> cbmExportDxf(Map<String, dynamic> plan) async {
    return postBytes('/plans/cbm-export-dxf', plan, auth: true);
  }

  static Future<dynamic> cbmCompliance(Map<String, dynamic> cbm, {String packId = 'pakistan_generic'}) async {
    return post('/plans/cbm-compliance', {'cbm': cbm, 'pack_id': packId}, auth: true);
  }

  static Future<void> saveSession(String token, Map<String, dynamic> user) async {
    if (token.isNotEmpty) {
      try {
        await _secureStorage.write(key: _secureTokenKey, value: token);
      } catch (_) {}
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('user', jsonEncode(user));
    // Clear legacy plaintext tokens
    await prefs.remove('token');
    await prefs.remove('nakshai_token');
  }

  static Future<Map<String, dynamic>?> currentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString('user');
    if (raw == null) return null;
    try { return Map<String, dynamic>.from(jsonDecode(raw)); } catch (_) { return null; }
  }

  static Future<void> logout() async {
    try {
      await _secureStorage.delete(key: _secureTokenKey);
    } catch (_) {}
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('token');
    await prefs.remove('nakshai_token');
    await prefs.remove('user');
    await prefs.remove('nakshai_user');
  }
}
