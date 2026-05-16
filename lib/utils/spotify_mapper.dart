import '../models/motion_analysis.dart';
import '../models/audio_analysis.dart';

class SpotifyMapper {
  /// Maps a motion analysis to Spotify search genre keywords.
  static List<String> fromMotion(MotionAnalysis analysis) {
    final bpm = analysis.bpm;
    final intensity = analysis.intensity;

    if (bpm < 80) {
      return intensity < 0.3
          ? ['ambient', 'chill', 'acoustic']
          : ['blues', 'soul', 'slow jazz'];
    }

    if (bpm < 100) {
      return intensity < 0.4
          ? ['indie', 'folk', 'singer-songwriter']
          : ['r&b', 'neo soul', 'pop'];
    }

    if (bpm < 120) {
      return intensity < 0.5
          ? ['pop', 'indie pop', 'soft rock']
          : ['hip hop', 'funk', 'disco'];
    }

    if (bpm < 140) {
      return intensity > 0.6
          ? ['latin', 'salsa', 'cha-cha']
          : ['dance pop', 'house', 'tropical'];
    }

    // bpm >= 140
    return intensity > 0.7
        ? ['electronic', 'edm', 'techno']
        : ['drum and bass', 'trance', 'dance'];
  }

  /// Maps an audio analysis to Spotify search genre keywords.
  static List<String> fromAudio(AudioAnalysis analysis) {
    final tempo = analysis.estimatedTempo;
    final energy = analysis.energy;
    final freq = analysis.dominantFrequency;

    // Low frequency dominant → bass-heavy
    if (freq < 200 && energy > 0.4) {
      return tempo > 120 ? ['hip hop', 'trap', 'bass'] : ['reggae', 'dub', 'bass music'];
    }

    // Mid-range dominant → vocal / melodic
    if (freq >= 200 && freq < 2000) {
      if (tempo < 90) return ['ballad', 'soul', 'acoustic'];
      if (tempo < 120) return ['pop', 'indie', 'r&b'];
      return ['dance pop', 'latin', 'afrobeats'];
    }

    // High frequency → energetic / bright
    if (tempo > 130) return ['electronic', 'edm', 'dance'];
    return ['pop rock', 'alternative', 'indie rock'];
  }

  /// Builds a Spotify search query string from genre keywords.
  static String buildSearchQuery(List<String> genres, {int limit = 3}) {
    final selected = genres.take(limit).toList();
    return selected.join(' ');
  }
}
