class MotionAnalysis {
  final double bpm;
  final double energy;
  final double intensity;
  final MotionPattern pattern;

  const MotionAnalysis({
    required this.bpm,
    required this.energy,
    required this.intensity,
    required this.pattern,
  });
}

enum MotionPattern {
  slow,
  medium,
  fast,
  chaotic,
}
