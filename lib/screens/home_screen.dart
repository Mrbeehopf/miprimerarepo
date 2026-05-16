import 'package:flutter/material.dart';
import 'package:permission_handler/permission_handler.dart';
import '../services/motion_service.dart';
import '../services/audio_service.dart';
import '../services/spotify_service.dart';
import '../utils/spotify_mapper.dart';
import 'results_screen.dart';
import '../widgets/motion_synth_button.dart';
import '../widgets/audio_synth_button.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final MotionService _motionService = MotionService();
  final AudioService _audioService = AudioService();
  final SpotifyService _spotify = SpotifyService();

  bool _motionRecording = false;
  bool _audioRecording = false;
  bool _searching = false;
  int _countdown = 5;
  String? _userName;
  String? _statusMessage;

  @override
  void initState() {
    super.initState();
    _loadUserName();
  }

  Future<void> _loadUserName() async {
    final name = await _spotify.getUserDisplayName();
    if (mounted) setState(() => _userName = name);
  }

  Future<void> _startMotionSynth() async {
    setState(() {
      _motionRecording = true;
      _countdown = 5;
      _statusMessage = 'Bewege dich!';
    });

    // Start recording and countdown in parallel
    final recordingFuture = _motionService.record(durationSeconds: 5);

    for (int i = 5; i > 0; i--) {
      if (!mounted) return;
      setState(() => _countdown = i);
      await Future.delayed(const Duration(seconds: 1));
    }

    if (!mounted) return;
    setState(() => _statusMessage = 'Analysiere Bewegung...');

    try {
      final analysis = await recordingFuture;
      final genres = SpotifyMapper.fromMotion(analysis);
      final query = SpotifyMapper.buildSearchQuery(genres);

      setState(() => _searching = true);
      final tracks = await _spotify.searchTracks(query);

      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResultsScreen(
            tracks: tracks,
            bpm: analysis.bpm,
            energy: analysis.intensity,
            source: AnalysisSource.motion,
          ),
        ),
      );
    } catch (e) {
      if (mounted) {
        _showError('Fehler bei der Bewegungsanalyse: $e');
      }
    } finally {
      if (mounted) {
        setState(() {
          _motionRecording = false;
          _searching = false;
          _statusMessage = null;
        });
      }
    }
  }

  Future<void> _startAudioRecording() async {
    final status = await Permission.microphone.request();
    if (!status.isGranted) {
      _showError('Mikrofonzugriff verweigert.');
      return;
    }

    await _audioService.startRecording();
    if (mounted) {
      setState(() {
        _audioRecording = true;
        _statusMessage = 'Aufnahme läuft...';
      });
    }
  }

  Future<void> _stopAudioRecording() async {
    if (!_audioRecording) return;

    setState(() {
      _audioRecording = false;
      _statusMessage = 'Analysiere Audio...';
    });

    try {
      final analysis = await _audioService.stopAndAnalyze();
      final genres = SpotifyMapper.fromAudio(analysis);
      final query = SpotifyMapper.buildSearchQuery(genres);

      setState(() => _searching = true);
      final tracks = await _spotify.searchTracks(query);

      if (!mounted) return;
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => ResultsScreen(
            tracks: tracks,
            bpm: analysis.estimatedTempo,
            energy: analysis.energy,
            source: AnalysisSource.audio,
          ),
        ),
      );
    } catch (e) {
      if (mounted) _showError('Fehler bei der Audio-Analyse: $e');
    } finally {
      if (mounted) setState(() {
        _searching = false;
        _statusMessage = null;
      });
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red.shade700,
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  void dispose() {
    _motionService.dispose();
    _audioService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      body: SafeArea(
        child: Column(
          children: [
            // Header
            _buildHeader(),

            const Spacer(),

            // Status message
            if (_statusMessage != null || _searching)
              Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: Column(
                  children: [
                    if (_searching) ...[
                      const CircularProgressIndicator(
                          color: Color(0xFF1DB954)),
                      const SizedBox(height: 10),
                    ],
                    Text(
                      _statusMessage ?? 'Suche Songs...',
                      style: const TextStyle(
                          color: Colors.white70, fontSize: 15),
                    ),
                  ],
                ),
              ),

            // Buttons row
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Motion-Synth
                  Column(
                    children: [
                      MotionSynthButton(
                        isRecording: _motionRecording,
                        countdown: _countdown,
                        onPressed:
                            _searching || _audioRecording ? () {} : _startMotionSynth,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Handy bewegen',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.5),
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),

                  // Divider
                  Container(
                    height: 180,
                    width: 1,
                    color: Colors.white.withOpacity(0.1),
                  ),

                  // Audio-Synth
                  AudioSynthButton(
                    isRecording: _audioRecording,
                    onRecordStart: _searching || _motionRecording
                        ? () {}
                        : _startAudioRecording,
                    onRecordStop: _stopAudioRecording,
                  ),
                ],
              ),
            ),

            const Spacer(),

            // Instructions footer
            Padding(
              padding: const EdgeInsets.only(bottom: 24),
              child: Text(
                'Tippe auf Motion-Synth oder halte Audio-Synth gedrückt',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.3),
                  fontSize: 12,
                ),
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Row(
        children: [
          const Icon(Icons.motion_photos_on,
              color: Color(0xFF1DB954), size: 28),
          const SizedBox(width: 10),
          const Text(
            'MotionSynth',
            style: TextStyle(
              color: Colors.white,
              fontSize: 22,
              fontWeight: FontWeight.bold,
              letterSpacing: 1,
            ),
          ),
          const Spacer(),
          if (_userName != null)
            Row(
              children: [
                const Icon(Icons.person, color: Color(0xFF1DB954), size: 18),
                const SizedBox(width: 6),
                Text(
                  _userName!,
                  style: const TextStyle(color: Colors.white70, fontSize: 13),
                ),
              ],
            ),
          IconButton(
            icon: const Icon(Icons.logout, color: Colors.white38, size: 20),
            onPressed: () async {
              await _spotify.logout();
              if (mounted) {
                Navigator.of(context)
                    .pushReplacementNamed('/auth');
              }
            },
          ),
        ],
      ),
    );
  }
}
