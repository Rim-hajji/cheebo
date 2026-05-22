import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/chat_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/history_screen.dart';
import 'screens/medications_screen.dart';
import 'screens/articles_screen.dart';
import 'services/notification_ws_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  runApp(const CheeboApp());
}

class CheeboApp extends StatelessWidget {
  const CheeboApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Cheebo Healthcare',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        useMaterial3: true,
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF7B56E2),
          secondary: Color(0xFF9A7BF2),
          surface: Color(0xFF1E1535),
          onPrimary: Colors.white,
          onSurface: Colors.white,
          error: Color(0xFFE25656),
        ),
        scaffoldBackgroundColor: const Color(0xFF0D0820),
        cardColor: const Color(0xFF1A1232),
        appBarTheme: const AppBarTheme(
          elevation: 0,
          backgroundColor: Color(0xFF1A1232),
          centerTitle: false,
          titleTextStyle: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Colors.white),
          iconTheme: IconThemeData(color: Colors.white),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF7B56E2),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            padding: const EdgeInsets.symmetric(vertical: 16),
            elevation: 6,
          ),
        ),
      ),
      home: const CheeboMainShell(),
    );
  }
}

class CheeboMainShell extends StatefulWidget {
  const CheeboMainShell({super.key});

  @override
  State<CheeboMainShell> createState() => _CheeboMainShellState();
}

class _CheeboMainShellState extends State<CheeboMainShell> {
  int _currentIndex = 0;

  // ── Notifications WebSocket ─────────────────────────────────────
  final NotificationWsService _notifService = NotificationWsService();
  StreamSubscription<Map<String, dynamic>>? _notifSub;
  Map<String, dynamic>? _activeNotif;
  Timer? _notifTimer;

  @override
  void initState() {
    super.initState();
    _notifService.connect();
    _notifSub = _notifService.stream.listen(_handleNotification);
  }

  @override
  void dispose() {
    _notifSub?.cancel();
    _notifService.dispose();
    _notifTimer?.cancel();
    super.dispose();
  }

  void _handleNotification(Map<String, dynamic> msg) {
    if (!mounted) return;
    final type = msg['type'] as String?;
    if (type == 'medication_reminder' || type == 'emergency_alert') {
      setState(() => _activeNotif = msg);
      _notifTimer?.cancel();
      // Fermeture automatique après 6 secondes
      _notifTimer = Timer(const Duration(seconds: 6), () {
        if (mounted) setState(() => _activeNotif = null);
      });
    }
  }

  void _dismissNotif() {
    _notifTimer?.cancel();
    setState(() => _activeNotif = null);
  }

  void goToChat() => setState(() => _currentIndex = 1);
  void goToMedications() => setState(() => _currentIndex = 3);

  @override
  Widget build(BuildContext context) {
    final screens = [
      const DashboardScreen(),
      const ChatScreen(),
      const HistoryScreen(),
      const MedicationsScreen(),
      const ArticlesScreen(),
    ];

    return Scaffold(
      body: Stack(
        children: [
          IndexedStack(index: _currentIndex, children: screens),
          // ── Bannière notification ───────────────────────────────
          if (_activeNotif != null)
            _NotificationBanner(
              notification: _activeNotif!,
              onDismiss: _dismissNotif,
              onTap: () {
                _dismissNotif();
                final type = _activeNotif?['type'];
                if (type == 'emergency_alert') goToChat();
                if (type == 'medication_reminder') goToMedications();
              },
            ),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: const Color(0xFF1A1232),
          border: const Border(top: BorderSide(color: Color(0xFF2D2050), width: 0.5)),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, -4)),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) => setState(() => _currentIndex = i),
          backgroundColor: Colors.transparent,
          elevation: 0,
          type: BottomNavigationBarType.fixed,
          selectedItemColor: const Color(0xFFC084FC),
          unselectedItemColor: const Color(0xFF4A3A6E),
          selectedLabelStyle: const TextStyle(fontWeight: FontWeight.bold, fontSize: 11, letterSpacing: 0.3),
          unselectedLabelStyle: const TextStyle(fontSize: 10, fontWeight: FontWeight.w500),
          items: const [
            BottomNavigationBarItem(
              icon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.dashboard_outlined, size: 22)),
              activeIcon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.dashboard_rounded, size: 24)),
              label: 'Tableau',
            ),
            BottomNavigationBarItem(
              icon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.chat_bubble_outline_rounded, size: 22)),
              activeIcon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.chat_bubble_rounded, size: 24)),
              label: 'Chat IA',
            ),
            BottomNavigationBarItem(
              icon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.history_rounded, size: 22)),
              activeIcon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.history_rounded, size: 24)),
              label: 'Historique',
            ),
            BottomNavigationBarItem(
              icon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.medication_rounded, size: 22)),
              activeIcon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.medication_rounded, size: 24)),
              label: 'Pilulier',
            ),
            BottomNavigationBarItem(
              icon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.article_rounded, size: 22)),
              activeIcon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.article_rounded, size: 24)),
              label: 'Articles',
            ),
          ],
        ),
      ),
    );
  }
}

// ── Bannière notification ─────────────────────────────────────────────

class _NotificationBanner extends StatefulWidget {
  final Map<String, dynamic> notification;
  final VoidCallback onDismiss;
  final VoidCallback onTap;

  const _NotificationBanner({
    required this.notification,
    required this.onDismiss,
    required this.onTap,
  });

  @override
  State<_NotificationBanner> createState() => _NotificationBannerState();
}

class _NotificationBannerState extends State<_NotificationBanner>
    with SingleTickerProviderStateMixin {
  late AnimationController _anim;
  late Animation<Offset> _slide;

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 350));
    _slide = Tween<Offset>(begin: const Offset(0, -1), end: Offset.zero)
        .animate(CurvedAnimation(parent: _anim, curve: Curves.easeOutCubic));
    _anim.forward();
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final type      = widget.notification['type'] as String? ?? '';
    final isEmerg   = type == 'emergency_alert';
    final message   = widget.notification['message'] as String? ?? '';
    final topPad    = MediaQuery.of(context).padding.top;

    final Color bgColor     = isEmerg ? const Color(0xFF2A1000) : const Color(0xFF1A1232);
    final Color borderColor = isEmerg ? const Color(0xFFFF9500) : const Color(0xFF7B56E2);
    final Color iconBg      = isEmerg ? const Color(0xFFFF9500) : const Color(0xFF7B56E2);
    final IconData icon     = isEmerg ? Icons.emergency_rounded : Icons.medication_rounded;

    return Positioned(
      top: 0,
      left: 0,
      right: 0,
      child: SlideTransition(
        position: _slide,
        child: GestureDetector(
          onTap: widget.onTap,
          child: Container(
            margin: EdgeInsets.fromLTRB(12, topPad + 8, 12, 0),
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
            decoration: BoxDecoration(
              color: bgColor,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: borderColor, width: 1.5),
              boxShadow: [
                BoxShadow(
                  color: borderColor.withOpacity(0.25),
                  blurRadius: 16,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Row(
              children: [
                Container(
                  width: 36, height: 36,
                  decoration: BoxDecoration(shape: BoxShape.circle, color: iconBg),
                  child: Icon(icon, color: Colors.white, size: 18),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    message,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      height: 1.4,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                GestureDetector(
                  onTap: widget.onDismiss,
                  child: const Icon(Icons.close_rounded, color: Color(0xFF8B7AB0), size: 18),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
