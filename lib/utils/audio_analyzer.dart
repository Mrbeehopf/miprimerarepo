import 'dart:math';
import 'dart:typed_data';
import '../models/audio_analysis.dart';

class AudioAnalyzer {
  /// Analyzes raw PCM Int16 samples and returns dominant frequency, tempo and energy.
  static AudioAnalysis analyze(Uint8List rawBytes, {int sampleRate = 44100}) {
    // Convert bytes to signed 16-bit samples
    final samples = <double>[];
    for (int i = 0; i + 1 < rawBytes.length; i += 2) {
      final low = rawBytes[i];
      final high = rawBytes[i + 1];
      int value = (high << 8) | low;
      if (value >= 32768) value -= 65536;
      samples.add(value / 32768.0);
    }

    if (samples.isEmpty) {
      return const AudioAnalysis(
        dominantFrequency: 440,
        estimatedTempo: 120,
        energy: 0.5,
      );
    }

    final energy = _calculateRmsEnergy(samples);
    final dominantFreq = _findDominantFrequency(samples, sampleRate);
    final tempo = _estimateTempoFromEnergy(samples, sampleRate);

    return AudioAnalysis(
      dominantFrequency: dominantFreq,
      estimatedTempo: tempo,
      energy: energy,
    );
  }

  static double _calculateRmsEnergy(List<double> samples) {
    final sum = samples.map((s) => s * s).reduce((a, b) => a + b);
    return sqrt(sum / samples.length).clamp(0.0, 1.0);
  }

  /// Simple DFT on first 1024 samples for performance.
  static double _findDominantFrequency(List<double> samples, int sampleRate) {
    const fftSize = 1024;
    final window = samples.take(fftSize).toList();
    while (window.length < fftSize) {
      window.add(0.0);
    }

    double maxMagnitude = 0;
    int maxBin = 1;

    // Only check up to Nyquist / 2 (human voice / clap range up to ~4kHz)
    final limit = fftSize ~/ 4;
    for (int k = 1; k < limit; k++) {
      double real = 0;
      double imag = 0;
      for (int n = 0; n < fftSize; n++) {
        final angle = -2 * pi * k * n / fftSize;
        real += window[n] * cos(angle);
        imag += window[n] * sin(angle);
      }
      final magnitude = sqrt(real * real + imag * imag);
      if (magnitude > maxMagnitude) {
        maxMagnitude = magnitude;
        maxBin = k;
      }
    }

    return maxBin * sampleRate / fftSize;
  }

  /// Envelope-based tempo estimation using amplitude peaks.
  static double _estimateTempoFromEnergy(List<double> samples, int sampleRate) {
    const frameSize = 512;
    final envelope = <double>[];
    for (int i = 0; i + frameSize < samples.length; i += frameSize) {
      final frame = samples.sublist(i, i + frameSize);
      envelope.add(frame.map((s) => s.abs()).reduce((a, b) => a + b) / frameSize);
    }

    if (envelope.isEmpty) return 120;

    final mean = envelope.reduce((a, b) => a + b) / envelope.length;
    final threshold = mean * 1.3;

    int peaks = 0;
    bool above = false;
    for (final v in envelope) {
      if (v > threshold && !above) {
        peaks++;
        above = true;
      } else if (v <= threshold) {
        above = false;
      }
    }

    final durationSeconds = samples.length / sampleRate;
    final beatsPerSecond = durationSeconds > 0 ? peaks / durationSeconds : 2.0;
    return (beatsPerSecond * 60).clamp(60.0, 200.0);
  }
}
