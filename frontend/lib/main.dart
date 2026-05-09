import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/chat_screen.dart';
import 'screens/dashboard_screen.dart';
import 'screens/history_screen.dart';
import 'screens/profile_screen.dart';

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

  void goToChat() => setState(() => _currentIndex = 1);

  @override
  Widget build(BuildContext context) {
    final screens = [
      const DashboardScreen(),
      const ChatScreen(),
      const HistoryScreen(),
      const ProfileScreen(),
    ];

    return Scaffold(
      body: IndexedStack(index: _currentIndex, children: screens),
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
              icon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.pets_rounded, size: 22)),
              activeIcon: Padding(padding: EdgeInsets.only(bottom: 3), child: Icon(Icons.pets_rounded, size: 24)),
              label: 'Mon Animal',
            ),
          ],
        ),
      ),
    );
  }
}
