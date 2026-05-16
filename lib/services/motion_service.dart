import 'dart:async';
import 'package:sensors_plus/sensors_plus.dart';
import '../models/motion_analysis.dart';
import '../utils/motion_analyzer.dart';

class MotionService {
  StreamSubscription<AccelerometerEvent>? _subscription;
  final List<List<double>> _samples = [];

  /// Records accelerometer data for [durationSeconds] seconds, then returns analysis.
  Future<MotionAnalysis> record({int durationSeconds = 5}) async {
    _samples.clear();

    final completer = Completer<MotionAnalysis>();

    _subscription = accelerometerEventStream(
      samplingPeriod: const Duration(milliseconds: 20), // ~50 Hz
    ).listen((event) {
      _samples.add([event.x, event.y, event.z]);
    });

    await Future.delayed(Duration(seconds: durationSeconds));
    await _subscription?.cancel();
    _subscription = null;

    final result = MotionAnalyzer.analyze(List.from(_samples));
    _samples.clear();
    completer.complete(result);

    return completer.future;
  }

  void dispose() {
    _subscription?.cancel();
  }
}
