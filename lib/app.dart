import 'package:flutter/material.dart';
import 'screens/auth_screen.dart';
import 'screens/home_screen.dart';

class MotionSynthApp extends StatelessWidget {
  const MotionSynthApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MotionSynth',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF1DB954),
          secondary: const Color(0xFF1DB954),
          surface: const Color(0xFF1e1e1e),
          background: const Color(0xFF121212),
        ),
        scaffoldBackgroundColor: const Color(0xFF121212),
        fontFamily: 'sans-serif',
        useMaterial3: true,
      ),
      initialRoute: '/auth',
      routes: {
        '/auth': (_) => const AuthScreen(),
        '/home': (_) => const HomeScreen(),
      },
    );
  }
}
