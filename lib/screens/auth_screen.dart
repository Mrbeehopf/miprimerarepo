import 'package:flutter/material.dart';
import '../services/spotify_service.dart';
import 'home_screen.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final SpotifyService _spotify = SpotifyService();
  bool _loading = false;
  String? _error;

  Future<void> _login() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final success = await _spotify.authenticate();

    if (!mounted) return;

    if (success) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    } else {
      setState(() {
        _loading = false;
        _error = 'Login fehlgeschlagen. Bitte überprüfe deine Spotify Client-ID in der .env Datei.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      body: SafeArea(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.motion_photos_on,
                    size: 80, color: Color(0xFF1DB954)),
                const SizedBox(height: 20),
                const Text(
                  'MotionSynth',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 2,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Musik durch Bewegung entdecken',
                  style: TextStyle(
                      color: Colors.white.withOpacity(0.6), fontSize: 14),
                ),
                const SizedBox(height: 60),
                if (_loading)
                  const CircularProgressIndicator(color: Color(0xFF1DB954))
                else
                  ElevatedButton.icon(
                    onPressed: _login,
                    icon: const Icon(Icons.login),
                    label: const Text('Mit Spotify anmelden'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF1DB954),
                      foregroundColor: Colors.black,
                      padding: const EdgeInsets.symmetric(
                          horizontal: 32, vertical: 16),
                      textStyle: const TextStyle(
                          fontSize: 16, fontWeight: FontWeight.bold),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30)),
                    ),
                  ),
                if (_error != null) ...[
                  const SizedBox(height: 24),
                  Text(
                    _error!,
                    style: const TextStyle(color: Colors.redAccent, fontSize: 13),
                    textAlign: TextAlign.center,
                  ),
                ],
                const SizedBox(height: 40),
                Text(
                  'Du benötigst eine Spotify-App in der Spotify Developer Console\nmit der Redirect-URI: motionsynth://callback',
                  style: TextStyle(
                      color: Colors.white.withOpacity(0.3), fontSize: 11),
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
