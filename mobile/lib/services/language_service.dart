import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

class LanguageService extends ChangeNotifier {
  LanguageService._();
  static final LanguageService instance = LanguageService._();

  static const String _storageKey = 'nakshai_lang';
  String _code = 'en';

  String get code => _code;
  bool get isUrdu => _code == 'ur';

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getString(_storageKey);
    if (saved == 'ur' || saved == 'en') {
      _code = saved!;
      notifyListeners();
    }
  }

  Future<void> setLanguage(String code) async {
    if (code != 'en' && code != 'ur') return;
    if (_code == code) return;
    _code = code;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, code);
  }

  Future<void> toggle() => setLanguage(isUrdu ? 'en' : 'ur');

  String t(String en, String ur) => isUrdu ? ur : en;
}

class LanguageScope extends InheritedNotifier<LanguageService> {
  const LanguageScope({super.key, required LanguageService service, required super.child}) : super(notifier: service);

  static LanguageService of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<LanguageScope>();
    return scope?.notifier ?? LanguageService.instance;
  }
}

String tr(BuildContext context, String en, String ur) => LanguageScope.of(context).t(en, ur);
