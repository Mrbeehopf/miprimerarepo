import 'dart:math';
import '../models/motion_analysis.dart';

class MotionAnalyzer {
  /// Analyzes collected accelerometer samples and returns BPM, energy, pattern.
  /// [samples] is a list of [x, y, z] acceleration vectors in m/s².
  static MotionAnalysis analyze(List<List<double>> samples) {
    if (samples.isEmpty) {
      return const MotionAnalysis(
        bpm: 120,
        energy: 0.5,
        intensity: 0.5,
        pattern: MotionPattern.medium,
      );
    }

    final magnitudes = samples.map((s) {
      return sqrt(s[0] * s[0] + s[1] * s[1] + s[2] * s[2]);
    }).toList();

    final energy = _calculateEnergy(magnitudes);
    final bpm = _estimateBpm(magnitudes);
    final intensity = (energy / 30.0).clamp(0.0, 1.0);
    final pattern = _classifyPattern(bpm, intensity);

    return MotionAnalysis(
      bpm: bpm,
      energy: energy,
      intensity: intensity,
      pattern: pattern,
    );
  }

  /// RMS of magnitudes, baseline gravity (~9.8 m/s²) subtracted.
  static double _calculateEnergy(List<double> magnitudes) {
    final rms = sqrt(magnitudes.map((m) => m * m).reduce((a, b) => a + b) / magnitudes.length);
    return (rms - 9.8).abs();
  }

  /// Peak detection: count peaks per second to derive BPM.
  /// Assumes 50 Hz sampling rate (samples per second).
  static double _estimateBpm(List<double> magnitudes) {
    const samplingRate = 50.0;
    final smoothed = _smooth(magnitudes, 5);
    final mean = smoothed.reduce((a, b) => a + b) / smoothed.length;
    final threshold = mean * 1.2;

    int peaks = 0;
    bool above = false;
    for (final v in smoothed) {
      if (v > threshold && !above) {
        peaks++;
        above = true;
      } else if (v <= threshold) {
        above = false;
      }
    }

    final seconds = smoothed.length / samplingRate;
    final beatsPerSecond = seconds > 0 ? peaks / seconds : 2.0;
    return (beatsPerSecond * 60).clamp(60.0, 200.0);
  }

  static List<double> _smooth(List<double> data, int windowSize) {
    final result = <double>[];
    for (int i = 0; i < data.length; i++) {
      final start = (i - windowSize ~/ 2).clamp(0, data.length - 1);
      final end = (i + windowSize ~/ 2 + 1).clamp(0, data.length);
      final window = data.sublist(start, end);
      result.add(window.reduce((a, b) => a + b) / window.length);
    }
    return result;
  }

  static MotionPattern _classifyPattern(double bpm, double intensity) {
    if (bpm < 90) return MotionPattern.slow;
    if (bpm < 120) return MotionPattern.medium;
    if (intensity > 0.7) return MotionPattern.chaotic;
    return MotionPattern.fast;
  }
}
