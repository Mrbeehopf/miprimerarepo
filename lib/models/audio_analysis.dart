class AudioAnalysis {
  final double dominantFrequency;
  final double estimatedTempo;
  final double energy;

  const AudioAnalysis({
    required this.dominantFrequency,
    required this.estimatedTempo,
    required this.energy,
  });
}
