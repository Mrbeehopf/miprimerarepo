import 'package:flutter/material.dart';

class MotionSynthButton extends StatefulWidget {
  final bool isRecording;
  final VoidCallback onPressed;
  final int countdown;

  const MotionSynthButton({
    super.key,
    required this.isRecording,
    required this.onPressed,
    this.countdown = 0,
  });

  @override
  State<MotionSynthButton> createState() => _MotionSynthButtonState();
}

class _MotionSynthButtonState extends State<MotionSynthButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void didUpdateWidget(MotionSynthButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isRecording) {
      _pulseController.repeat(reverse: true);
    } else {
      _pulseController.stop();
      _pulseController.reset();
    }
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _pulseAnimation,
      builder: (context, child) {
        return Transform.scale(
          scale: widget.isRecording ? _pulseAnimation.value : 1.0,
          child: GestureDetector(
            onTap: widget.isRecording ? null : widget.onPressed,
            child: Container(
              width: 160,
              height: 160,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: widget.isRecording
                      ? [const Color(0xFF1DB954), const Color(0xFF158a3c)]
                      : [const Color(0xFF2d2d2d), const Color(0xFF1a1a1a)],
                ),
                boxShadow: [
                  BoxShadow(
                    color: widget.isRecording
                        ? const Color(0xFF1DB954).withOpacity(0.5)
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
                    widget.isRecording ? Icons.sensors : Icons.motion_photos_on,
                    size: 48,
                    color: Colors.white,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.isRecording
                        ? (widget.countdown > 0 ? '${widget.countdown}s' : 'Analysiere...')
                        : 'Motion-Synth',
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
        );
      },
    );
  }
}
