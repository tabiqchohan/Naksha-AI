import 'package:flutter/material.dart';
import 'screens/floor_plan_editor_screen.dart';

void main() {
  runApp(const NakshaAIApp());
}

class NakshaAIApp extends StatelessWidget {
  const NakshaAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'NakshaAI Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0284C7)),
        useMaterial3: true,
        fontFamily: 'Roboto',
      ),
      home: const FloorPlanEditorScreen(),
    );
  }
}
