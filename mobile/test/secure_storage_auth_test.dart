import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:nakshai_mobile/services/api_service.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  final Map<String, String> mockSecureStorage = {};

  setUp(() {
    mockSecureStorage.clear();
    SharedPreferences.setMockInitialValues({});

    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'), (methodCall) async {
      switch (methodCall.method) {
        case 'read':
          final key = methodCall.arguments['key'];
          return mockSecureStorage[key];
        case 'write':
          final key = methodCall.arguments['key'];
          final value = methodCall.arguments['value'];
          mockSecureStorage[key] = value;
          return null;
        case 'delete':
          final key = methodCall.arguments['key'];
          mockSecureStorage.remove(key);
          return null;
        case 'deleteAll':
          mockSecureStorage.clear();
          return null;
        default:
          return null;
      }
    });
  });

  tearDown(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'), null);
  });

  group('A2.2 Secure Storage & Session Management Tests', () {
    test('1. Secure token save and read', () async {
      await ApiService.saveSession('secure_jwt_token_123', {'username': 'testuser'});
      final token = await ApiService.token();
      expect(token, 'secure_jwt_token_123');
      expect(await ApiService.isLoggedIn(), isTrue);
    });

    test('2. Missing token behavior returns null and isLoggedIn false', () async {
      final token = await ApiService.token();
      expect(token, isNull);
      expect(await ApiService.isLoggedIn(), isFalse);
    });

    test('3. Legacy SharedPreferences migration to secure storage', () async {
      SharedPreferences.setMockInitialValues({'token': 'legacy_token_abc'});

      final token = await ApiService.token();
      expect(token, 'legacy_token_abc');
      expect(mockSecureStorage['nakshai_secure_token'], 'legacy_token_abc');

      final prefs = await SharedPreferences.getInstance();
      expect(prefs.getString('token'), isNull);
    });

    test('4. Existing secure token preservation over legacy token', () async {
      mockSecureStorage['nakshai_secure_token'] = 'existing_secure_token';
      SharedPreferences.setMockInitialValues({'token': 'old_legacy_token'});

      final token = await ApiService.token();
      expect(token, 'existing_secure_token');
    });

    test('5. Logout clears secure token and user preferences', () async {
      await ApiService.saveSession('token_to_clear', {'username': 'user'});
      expect(await ApiService.isLoggedIn(), isTrue);

      await ApiService.logout();
      expect(await ApiService.token(), isNull);
      expect(await ApiService.isLoggedIn(), isFalse);
      expect(await ApiService.currentUser(), isNull);
    });

    test('6. Public requests have no authorization header', () async {
      final headers = await ApiService.headers(json: true, auth: false);
      expect(headers.containsKey('Authorization'), isFalse);
      expect(headers['Content-Type'], 'application/json');
    });

    test('7. Authenticated requests include Bearer token when logged in', () async {
      await ApiService.saveSession('bearer_token_xyz', {'username': 'auth_user'});
      final headers = await ApiService.headers(json: true, auth: true);
      expect(headers['Authorization'], 'Bearer bearer_token_xyz');
    });

    test('8. Missing token on auth request does not produce malformed Bearer header', () async {
      final headers = await ApiService.headers(json: true, auth: true);
      expect(headers.containsKey('Authorization'), isFalse);
    });
  });
}
