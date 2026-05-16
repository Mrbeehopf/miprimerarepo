import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import '../models/spotify_track.dart';

class TrackCard extends StatelessWidget {
  final SpotifyTrack track;
  final VoidCallback onPlay;

  const TrackCard({super.key, required this.track, required this.onPlay});

  @override
  Widget build(BuildContext context) {
    return Card(
      color: const Color(0xFF1e1e1e),
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: track.albumArtUrl != null
              ? CachedNetworkImage(
                  imageUrl: track.albumArtUrl!,
                  width: 56,
                  height: 56,
                  fit: BoxFit.cover,
                  placeholder: (_, __) => _placeholder(),
                  errorWidget: (_, __, ___) => _placeholder(),
                )
              : _placeholder(),
        ),
        title: Text(
          track.name,
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.w600,
            fontSize: 14,
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        subtitle: Text(
          track.artist,
          style: TextStyle(color: Colors.white.withOpacity(0.6), fontSize: 12),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: IconButton(
          icon: const Icon(Icons.play_circle_filled_rounded,
              color: Color(0xFF1DB954), size: 36),
          onPressed: onPlay,
          tooltip: 'In Spotify öffnen',
        ),
      ),
    );
  }

  Widget _placeholder() {
    return Container(
      width: 56,
      height: 56,
      color: const Color(0xFF333333),
      child: const Icon(Icons.music_note, color: Colors.white54, size: 28),
    );
  }
}
