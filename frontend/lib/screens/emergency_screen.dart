import 'package:flutter/material.dart';

const kBgDark = Color(0xFF120C24);
const kBgCard = Color(0xFF1E1535);
const kPrimary = Color(0xFF7B56E2);

class EmergencyScreen extends StatefulWidget {
  final Map<String, dynamic> data;

  const EmergencyScreen({super.key, required this.data});

  @override
  State<EmergencyScreen> createState() => _EmergencyScreenState();
}

class _EmergencyScreenState extends State<EmergencyScreen> with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late Animation<double> _scaleAnim;

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    )..repeat(reverse: true);
    _scaleAnim = Tween<double>(begin: 0.92, end: 1.08).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final emergencyInfo = widget.data['results']?['emergency'] ?? {};
    final analysis = widget.data['analysis'] ?? {};
    final score = analysis['urgency_score'] ?? 10;
    final sentimentScore = analysis['sentiment_score'] ?? 50;
    final message = emergencyInfo['message_urgence'] ?? 'Urgence vitale possible. Contactez un vétérinaire immédiatement.';

    String empathicMessage = '';
    if (sentimentScore <= 30) {
      empathicMessage = 'Respirez. Restez calme. Votre animal a besoin de vous maintenant.';
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0E0B18),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.only(left: 24, right: 24, top: 24, bottom: 70),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Top bar
              Row(
                children: [
                  GestureDetector(
                    onTap: () => Navigator.pop(context),
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(12),
                        color: Colors.white.withOpacity(0.06),
                      ),
                      child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18),
                    ),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Colors.red.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: Colors.red.withOpacity(0.3)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.circle, size: 8, color: Colors.redAccent),
                        const SizedBox(width: 6),
                        Text('Score $score/10', style: const TextStyle(color: Colors.redAccent, fontSize: 12, fontWeight: FontWeight.bold)),
                      ],
                    ),
                  ),
                ],
              ),
              const Spacer(),

              // Pulsing alert icon
              Center(
                child: AnimatedBuilder(
                  animation: _scaleAnim,
                  builder: (ctx, child) => Transform.scale(
                    scale: _scaleAnim.value,
                    child: child,
                  ),
                  child: Container(
                    width: 120, height: 120,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: Colors.red.withOpacity(0.12),
                      boxShadow: [
                        BoxShadow(color: Colors.red.withOpacity(0.3), blurRadius: 40, spreadRadius: 8),
                      ],
                    ),
                    child: const Center(child: Text('🚨', style: TextStyle(fontSize: 60))),
                  ),
                ),
              ),
              const SizedBox(height: 28),

              const Text('URGENCE VÉTÉRINAIRE', textAlign: TextAlign.center,
                style: TextStyle(color: Colors.redAccent, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
              const SizedBox(height: 10),
              if (empathicMessage.isNotEmpty)
                Text(empathicMessage, textAlign: TextAlign.center,
                  style: const TextStyle(color: Colors.white60, fontSize: 14, fontStyle: FontStyle.italic, height: 1.5)),
              const SizedBox(height: 28),

              // Message card
              Container(
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A0A0A),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.red.withOpacity(0.25)),
                ),
                child: Text(message,
                  style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.6),
                  textAlign: TextAlign.center,
                ),
              ),
              const Spacer(),

              // CTA Buttons
              ElevatedButton.icon(
                icon: const Icon(Icons.phone_rounded),
                label: const Text('APPELER LES URGENCES', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red.shade600,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  elevation: 8,
                  shadowColor: Colors.red.withOpacity(0.5),
                ),
                onPressed: () {},
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => Navigator.pop(context),
                style: OutlinedButton.styleFrom(
                  side: BorderSide(color: Colors.white.withOpacity(0.15)),
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                ),
                child: const Text('Retour', style: TextStyle(fontSize: 16)),
              ),
              const SizedBox(height: 12),
            ],
          ),
        ),
      ),
    );
  }
}
