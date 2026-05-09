import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../services/api_service.dart';
import 'results_screen.dart';
import 'emergency_screen.dart';
import 'history_screen.dart';
import 'profile_screen.dart';
import 'settings_screen.dart';
import 'chat_screen.dart';

// Cheebo Brand Colors
const kBgDark = Color(0xFF120C24);
const kBgCard = Color(0xFF1E1535);
const kPrimary = Color(0xFF7B56E2);
const kSecondary = Color(0xFF9A7BF2);
const kAccent = Color(0xFFC084FC);

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;
  late stt.SpeechToText _speech;
  bool _isListening = false;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    )..repeat(reverse: true);
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.12).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _controller.dispose();
    super.dispose();
  }

  void _listen() async {
    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) {
          if (val == 'done' || val == 'notListening') {
            if (mounted) setState(() => _isListening = false);
          }
        },
        onError: (val) => debugPrint('onError: $val'),
      );
      if (available) {
        setState(() => _isListening = true);
        _speech.listen(
          onResult: (val) => setState(() => _controller.text = val.recognizedWords),
          localeId: 'fr_FR',
        );
      }
    } else {
      setState(() => _isListening = false);
      _speech.stop();
    }
  }

  Future<void> _analyze() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() => _isLoading = true);
    if (_isListening) {
      _speech.stop();
      _isListening = false;
    }

    try {
      final result = await ApiService.analyzeSymptoms(text);
      if (!mounted) return;
      final label = result['analysis']['urgency_label'];
      if (label == 'CRITICAL' || label == 'HIGH') {
        Navigator.push(context, MaterialPageRoute(builder: (_) => EmergencyScreen(data: result)));
      } else {
        Navigator.push(context, MaterialPageRoute(builder: (_) => ResultsScreen(data: result)));
      }
      _controller.clear();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Erreur de connexion: $e'),
          backgroundColor: const Color(0xFFE25656),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBgDark,
      drawer: _buildDrawer(context),
      body: Stack(
        children: [
          // Paw prints background pattern
          Positioned.fill(child: _buildPawPattern()),
          // Main content
          SafeArea(
            child: Column(
              children: [
                _buildTopBar(context),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const SizedBox(height: 24),
                        _buildHeader(),
                        const SizedBox(height: 36),
                        _buildServiceButtons(context),
                        const SizedBox(height: 36),
                        _buildInputCard(),
                        const SizedBox(height: 24),
                        _buildAnalyzeButton(),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPawPattern() {
    return CustomPaint(painter: _PawPatternPainter());
  }

  Widget _buildTopBar(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          IconButton(
            icon: const Icon(Icons.menu, color: Colors.white, size: 28),
            onPressed: () => Scaffold.of(context).openDrawer(),
          ),
          // Cheebo Logo text
          RichText(
            text: const TextSpan(
              children: [
                TextSpan(text: 'Chee', style: TextStyle(color: kPrimary, fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: -0.5)),
                TextSpan(text: 'bo', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: -0.5)),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.history, color: Colors.white, size: 28),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen())),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Column(
      children: [
        // Big Cheebo circle avatar
        Container(
          width: 90,
          height: 90,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: kPrimary.withOpacity(0.15),
            border: Border.all(color: kPrimary.withOpacity(0.4), width: 2),
          ),
          child: const Center(
            child: Text('🐾', style: TextStyle(fontSize: 42)),
          ),
        ),
        const SizedBox(height: 20),
        const Text(
          'Healthcare.',
          style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Colors.white, letterSpacing: -1),
        ),
        const SizedBox(height: 8),
        const Text(
          "Décrivez les symptômes de votre animal.\nNous analysons et guidons.",
          style: TextStyle(fontSize: 14, color: Color(0xFFB0A0CC), height: 1.5),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }

  Widget _buildServiceButtons(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
      children: [
        _buildServiceButton(
          emoji: '🩺',
          label: 'Analyser',
          color: kPrimary,
          onTap: null, // stays here
        ),
        _buildServiceButton(
          emoji: '📋',
          label: 'Historique',
          color: const Color(0xFF4B6BE2),
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen())),
        ),
        _buildServiceButton(
          emoji: '🐶',
          label: 'Profil',
          color: const Color(0xFF6B56C2),
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen())),
        ),
      ],
    );
  }

  Widget _buildServiceButton({required String emoji, required String label, required Color color, VoidCallback? onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withOpacity(0.18),
              border: Border.all(color: color.withOpacity(0.4), width: 1.5),
            ),
            child: Center(child: Text(emoji, style: const TextStyle(fontSize: 30))),
          ),
          const SizedBox(height: 8),
          Text(label, style: const TextStyle(color: Color(0xFFB0A0CC), fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildInputCard() {
    return Container(
      decoration: BoxDecoration(
        color: kBgCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: kPrimary.withOpacity(0.3), width: 1.5),
        boxShadow: [
          BoxShadow(color: kPrimary.withOpacity(0.08), blurRadius: 20, offset: const Offset(0, 6)),
        ],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Décrivez la situation', style: TextStyle(color: kSecondary, fontWeight: FontWeight.bold, fontSize: 13, letterSpacing: 0.5)),
          const SizedBox(height: 12),
          TextField(
            controller: _controller,
            maxLines: 4,
            style: const TextStyle(color: Colors.white, fontSize: 15, height: 1.5),
            decoration: InputDecoration(
              hintText: 'Ex: Mon chien vomit depuis ce matin et refuse de boire...',
              hintStyle: const TextStyle(color: Color(0xFF6B5A8E), fontSize: 14),
              border: InputBorder.none,
              contentPadding: EdgeInsets.zero,
              suffixIcon: AnimatedBuilder(
                animation: _pulseAnimation,
                builder: (_, child) => Transform.scale(
                  scale: _isListening ? _pulseAnimation.value : 1.0,
                  child: child,
                ),
                child: IconButton(
                  icon: Icon(
                    _isListening ? Icons.mic : Icons.mic_none,
                    color: _isListening ? Colors.redAccent : kSecondary,
                    size: 28,
                  ),
                  onPressed: _listen,
                ),
              ),
            ),
          ),
          if (_isListening)
            const Padding(
              padding: EdgeInsets.only(top: 8),
              child: Row(
                children: [
                  Icon(Icons.fiber_manual_record, color: Colors.redAccent, size: 10),
                  SizedBox(width: 6),
                  Text('Écoute en cours...', style: TextStyle(color: Colors.redAccent, fontSize: 12, fontStyle: FontStyle.italic)),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildAnalyzeButton() {
    return SizedBox(
      height: 56,
      child: ElevatedButton(
        onPressed: _isLoading ? null : _analyze,
        style: ElevatedButton.styleFrom(
          backgroundColor: kPrimary,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          elevation: 8,
          shadowColor: kPrimary.withOpacity(0.5),
        ),
        child: _isLoading
            ? const SizedBox(height: 24, width: 24, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
            : const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.auto_awesome, size: 20),
                  SizedBox(width: 10),
                  Text('Analyser avec l\'IA', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, letterSpacing: 0.3)),
                ],
              ),
      ),
    );
  }

  Drawer _buildDrawer(BuildContext context) {
    return Drawer(
      backgroundColor: kBgCard,
      child: ListView(
        padding: EdgeInsets.zero,
        children: [
          DrawerHeader(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFF3D2B8E), kPrimary],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const Text('🐾', style: TextStyle(fontSize: 40)),
                const SizedBox(height: 8),
                RichText(
                  text: const TextSpan(children: [
                    TextSpan(text: 'Chee', style: TextStyle(color: kAccent, fontSize: 26, fontWeight: FontWeight.w900)),
                    TextSpan(text: 'bo', style: TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w900)),
                  ]),
                ),
                const Text('Healthcare', style: TextStyle(color: Colors.white60, fontSize: 12, letterSpacing: 1.5)),
              ],
            ),
          ),
          _drawerItem(Icons.home_rounded, 'Accueil', () => Navigator.pop(context)),
          _drawerItem(Icons.pets_rounded, 'Profil de l\'animal', () {
            Navigator.pop(context);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const ProfileScreen()));
          }),
          _drawerItem(Icons.history_rounded, 'Historique', () {
            Navigator.pop(context);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const HistoryScreen()));
          }),
          const Divider(color: Color(0xFF3D2E6E)),
          _drawerItem(Icons.settings_rounded, 'Paramètres', () {
            Navigator.pop(context);
            Navigator.push(context, MaterialPageRoute(builder: (_) => const SettingsScreen()));
          }),
        ],
      ),
    );
  }

  Widget _drawerItem(IconData icon, String label, VoidCallback onTap) {
    return ListTile(
      leading: Icon(icon, color: kSecondary),
      title: Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
      onTap: onTap,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    );
  }
}

// Custom paw print pattern painter
class _PawPatternPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF7B56E2).withOpacity(0.04)
      ..style = PaintingStyle.fill;

    // Draw subtle paw shapes all over the background
    final offsets = [
      Offset(size.width * 0.1, size.height * 0.08),
      Offset(size.width * 0.75, size.height * 0.12),
      Offset(size.width * 0.45, size.height * 0.28),
      Offset(size.width * 0.85, size.height * 0.4),
      Offset(size.width * 0.15, size.height * 0.55),
      Offset(size.width * 0.6, size.height * 0.65),
      Offset(size.width * 0.3, size.height * 0.82),
      Offset(size.width * 0.9, size.height * 0.85),
    ];

    for (final offset in offsets) {
      _drawPaw(canvas, offset, 22, paint);
    }
  }

  void _drawPaw(Canvas canvas, Offset center, double size, Paint paint) {
    // Main pad
    canvas.drawOval(
      Rect.fromCenter(center: center, width: size, height: size * 0.85),
      paint,
    );
    // Toe pads
    final toeSize = size * 0.32;
    final offsets = [
      Offset(center.dx - size * 0.38, center.dy - size * 0.52),
      Offset(center.dx, center.dy - size * 0.62),
      Offset(center.dx + size * 0.38, center.dy - size * 0.52),
    ];
    for (final o in offsets) {
      canvas.drawCircle(o, toeSize, paint);
    }
  }

  @override
  bool shouldRepaint(_) => false;
}
