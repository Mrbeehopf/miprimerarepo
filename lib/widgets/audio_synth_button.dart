import 'package:flutter/material.dart';

class AudioSynthButton extends StatefulWidget {
  final bool isRecording;
  final VoidCallback onRecordStart;
  final VoidCallback onRecordStop;

  const AudioSynthButton({
    super.key,
    required this.isRecording,
    required this.onRecordStart,
    required this.onRecordStop,
  });

  @override
  State<AudioSynthButton> createState() => _AudioSynthButtonState();
}

class _AudioSynthButtonState extends State<AudioSynthButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _waveController;
  late Animation<double> _waveAnimation;

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _waveAnimation = Tween<double>(begin: 0.9, end: 1.1).animate(
      CurvedAnimation(parent: _waveController, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(AudioSynthButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isRecording) {
      _waveController.repeat(reverse: true);
    } else {
      _waveController.stop();
      _waveController.reset();
    }
  }

  @override
  void dispose() {
    _waveController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _waveAnimation,
      builder: (context, child) {
        return GestureDetector(
          onLongPressStart: (_) => widget.onRecordStart(),
          onLongPressEnd: (_) => widget.onRecordStop(),
          child: Column(
            children: [
              Transform.scale(
                scale: widget.isRecording ? _waveAnimation.value : 1.0,
                child: Container(
                  width: 160,
                  height: 160,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: widget.isRecording
                          ? [const Color(0xFFe91e63), const Color(0xFF880e4f)]
                          : [const Color(0xFF2d2d2d), const Color(0xFF1a1a1a)],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: widget.isRecording
                            ? const Color(0xFFe91e63).withOpacity(0.5)
                            : Colors.black45,
                        blurRadius: widget.isRecording ? 30 : 10,
                        spreadRadius: widget.isRecording ? 10 : 2,
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        widget.isRecording ? Icons.mic : Icons.mic_none,
                        size: 48,
                        color: Colors.white,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        widget.isRecording ? 'Aufnehmen...' : 'Audio-Synth',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                widget.isRecording
                    ? 'Loslassen zum Stoppen'
                    : 'Gedrückt halten & summen',
                style: TextStyle(
                  color: Colors.white.withOpacity(0.6),
                  fontSize: 11,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
