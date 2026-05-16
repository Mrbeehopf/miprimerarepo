import 'package:flutter/material.dart';
import '../models/spotify_track.dart';
import '../services/spotify_service.dart';
import '../widgets/track_card.dart';

enum AnalysisSource { motion, audio }

class ResultsScreen extends StatefulWidget {
  final List<SpotifyTrack> tracks;
  final double bpm;
  final double energy;
  final AnalysisSource source;

  const ResultsScreen({
    super.key,
    required this.tracks,
    required this.bpm,
    required this.energy,
    required this.source,
  });

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  final SpotifyService _spotify = SpotifyService();

  String get _sourceLabel =>
      widget.source == AnalysisSource.motion ? 'Bewegung' : 'Audio';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      appBar: AppBar(
        backgroundColor: const Color(0xFF121212),
        foregroundColor: Colors.white,
        title: const Text('Vorschläge'),
        actions: [
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.of(context).pop(),
            tooltip: 'Neue Suche',
          ),
        ],
      ),
      body: Column(
        children: [
          // Analysis info banner
          Container(
            margin: const EdgeInsets.all(16),
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            decoration: BoxDecoration(
              color: const Color(0xFF1e1e1e),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: const Color(0xFF1DB954).withOpacity(0.4),
                width: 1,
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _statChip(
                  icon: widget.source == AnalysisSource.motion
                      ? Icons.motion_photos_on
                      : Icons.mic,
                  label: _sourceLabel,
                  value: '',
                ),
                _statChip(
                  icon: Icons.speed,
                  label: 'BPM',
                  value: widget.bpm.toStringAsFixed(0),
                ),
                _statChip(
                  icon: Icons.bolt,
                  label: 'Energie',
                  value: '${(widget.energy * 100).toStringAsFixed(0)}%',
                ),
              ],
            ),
          ),

          // Track count
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: Row(
              children: [
                Text(
                  '${widget.tracks.length} Songs gefunden',
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.5),
                    fontSize: 13,
                  ),
                ),
              ],
            ),
          ),

          // Track list
          Expanded(
            child: widget.tracks.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(Icons.search_off,
                            size: 48, color: Colors.white.withOpacity(0.3)),
                        const SizedBox(height: 12),
                        Text(
                          'Keine Songs gefunden.\nBitte Spotify-Token prüfen.',
                          style: TextStyle(
                              color: Colors.white.withOpacity(0.4),
                              fontSize: 14),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    itemCount: widget.tracks.length,
                    itemBuilder: (context, index) {
                      final track = widget.tracks[index];
                      return TrackCard(
                        track: track,
                        onPlay: () => _spotify.openTrack(track),
                      );
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.of(context).pop(),
        backgroundColor: const Color(0xFF1DB954),
        foregroundColor: Colors.black,
        icon: const Icon(Icons.refresh),
        label: const Text('Neue Suche'),
      ),
    );
  }

  Widget _statChip({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Column(
      children: [
        Icon(icon, color: const Color(0xFF1DB954), size: 22),
        const SizedBox(height: 4),
        Text(
          value.isEmpty ? label : value,
          style: const TextStyle(
              color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
        ),
        if (value.isNotEmpty)
          Text(
            label,
            style: TextStyle(
                color: Colors.white.withOpacity(0.5), fontSize: 11),
          ),
      ],
    );
  }
}
