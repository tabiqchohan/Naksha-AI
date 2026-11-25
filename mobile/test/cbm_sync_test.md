# NAKSHA AI — Flutter Mobile App Phase A2.3 Testing Guide
## CBM-Based 2D Editor & 3D Synchronization

## 1. Prerequisites
- Flutter SDK installed (Dart `>=3.0.0 <4.0.0`).
- Flutter mobile project directory: `mobile/`.

---

## 2. Running Automated Tests
To run the complete automated test suite (API compatibility, secure storage auth, and CBM synchronization models):

```bash
cd mobile
flutter test
```

### Expected Output:
```text
00:01 +15: All tests passed!
```

---

## 3. Running Static Analysis
To run Flutter static analysis (`flutter analyze`):

```bash
cd mobile
flutter analyze
```

### Expected Output:
```text
Analyzing mobile...                                             
No issues found!
```

---

## 4. Test Suite Breakdown
1. **API Compatibility & CBM Helpers** (`mobile/test/api_compatibility_test.dart`): 4 tests verifying model parsing and CBM endpoint helper configuration.
2. **Secure Storage & Session Management** (`mobile/test/secure_storage_auth_test.dart`): 8 tests verifying secure token storage, legacy SharedPreferences migration, logout cleanup, and 401 handling.
3. **CBM Model & Synchronization** (`mobile/test/cbm_sync_test.dart`): 3 tests verifying site geometry parsing, canonical building model JSON round-tripping, stable ID preservation, and coordinate mapping.
