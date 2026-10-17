library hr_oto_design_system;

import 'package:flutter/material.dart';

class HrOtoTheme {
  static const _blue = Color(0xFF087CFF);
  static const _cyan = Color(0xFF19D8F2);

  static ThemeData light() => _theme(Brightness.light, Colors.white, const Color(0xFFF4F7FB));
  static ThemeData dark() => _theme(Brightness.dark, const Color(0xFF0B101A), const Color(0xFF121A27));

  static ThemeData _theme(Brightness brightness, Color surface, Color scaffold) {
    final scheme = ColorScheme.fromSeed(seedColor: _blue, brightness: brightness).copyWith(
      primary: _blue,
      secondary: _cyan,
      surface: surface,
    );
    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: scaffold,
      fontFamily: 'sans',
      cardTheme: const CardThemeData(margin: EdgeInsets.zero),
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
    );
  }
}

class HrOtoLogo extends StatelessWidget {
  const HrOtoLogo({super.key, this.size = 72});
  final double size;

  @override
  Widget build(BuildContext context) => Image.asset(
        'packages/hr_oto_design_system/assets/oto-hr-logo.png',
        width: size,
        height: size,
        fit: BoxFit.cover,
        semanticLabel: 'OTO-HR logo',
      );
}

class HrOtoShell extends StatelessWidget {
  const HrOtoShell({super.key, required this.productName, required this.subtitle, required this.onToggleTheme});
  final String productName;
  final String subtitle;
  final VoidCallback onToggleTheme;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(productName, style: const TextStyle(fontWeight: FontWeight.w700)),
        actions: [IconButton(onPressed: onToggleTheme, icon: const Icon(Icons.brightness_6_outlined))],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  const HrOtoLogo(size: 128),
                  const SizedBox(height: 24),
                  Text(productName, style: theme.textTheme.headlineMedium?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  Text(subtitle, textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
                  const SizedBox(height: 24),
                  const Chip(avatar: Icon(Icons.check_circle_outline), label: Text('Foundation მზად არის')),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

