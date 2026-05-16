import 'dart:io';
import 'dart:typed_data';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import '../models/audio_analysis.dart';
import '../utils/audio_analyzer.dart';

class AudioService {
  final AudioRecorder _recorder = AudioRecorder();
  String? _tempPath;

  Future<bool> hasPermission() async {
    return await _recorder.hasPermission();
  }

  Future<void> startRecording() async {
    final dir = await getTemporaryDirectory();
    _tempPath = '${dir.path}/motion_synth_recording.pcm';

    await _recorder.start(
      const RecordConfig(
        encoder: AudioEncoder.pcm16bits,
        sampleRate: 44100,
        numChannels: 1,
      ),
      path: _tempPath!,
    );
  }

  /// Stops the recording and returns the audio analysis.
  Future<AudioAnalysis> stopAndAnalyze() async {
    final path = await _recorder.stop();
    if (path == null) {
      return const AudioAnalysis(
        dominantFrequency: 440,
        estimatedTempo: 120,
        energy: 0.5,
      );
    }

    final file = File(path);
    if (!await file.exists()) {
      return const AudioAnalysis(
        dominantFrequency: 440,
        estimatedTempo: 120,
        energy: 0.5,
      );
    }

    final Uint8List bytes = await file.readAsBytes();
    await file.delete();

    return AudioAnalyzer.analyze(bytes);
  }

  Future<bool> isRecording() async {
    return await _recorder.isRecording();
  }

  void dispose() {
    _recorder.dispose();
  }
}
