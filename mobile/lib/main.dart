import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'services/language_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await LanguageService.instance.load();
  runApp(const NakshaAIApp());
}

class NakshaAIApp extends StatelessWidget {
  const NakshaAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: LanguageService.instance,
      builder: (context, _) {
        final language = LanguageService.instance;
        return LanguageScope(
          service: language,
          child: MaterialApp(
            title: 'NakshaAI Mobile',
            debugShowCheckedModeBanner: false,
            theme: ThemeData(
              colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0284C7)),
              useMaterial3: true,
              fontFamily: 'Roboto',
            ),
            builder: (context, child) => Directionality(
              textDirection: language.isUrdu ? TextDirection.rtl : TextDirection.ltr,
              child: child ?? const SizedBox.shrink(),
            ),
            home: const HomeScreen(),
          ),
        );
      },
    );
  }
}
