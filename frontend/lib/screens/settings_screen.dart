import 'package:flutter/material.dart';

const kBgCard = Color(0xFF1E1535);
const kPrimary = Color(0xFF7B56E2);
const kSecondary = Color(0xFF9A7BF2);

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF120C24),
      appBar: AppBar(
        backgroundColor: kBgCard,
        title: const Text('Paramètres', style: TextStyle(fontWeight: FontWeight.bold)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          _buildSection('Application', [
            _buildTile(Icons.notifications_rounded, 'Notifications', 'Gérer les alertes'),
            _buildTile(Icons.language_rounded, 'Langue', 'Français'),
            _buildTile(Icons.dark_mode_rounded, 'Thème', 'Sombre'),
          ]),
          const SizedBox(height: 20),
          _buildSection('À propos', [
            _buildTile(Icons.info_rounded, 'Version', '1.0.0'),
            _buildTile(Icons.privacy_tip_rounded, 'Confidentialité', 'Politique de données'),
            _buildTile(Icons.pets_rounded, 'À propos de Cheebo', 'NeuralBey'),
          ]),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> items) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(title.toUpperCase(), style: const TextStyle(color: kSecondary, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: kBgCard,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFF3D2E6E)),
          ),
          child: Column(children: items),
        ),
      ],
    );
  }

  Widget _buildTile(IconData icon, String title, String subtitle) {
    return ListTile(
      leading: Icon(icon, color: kSecondary),
      title: Text(title, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500)),
      subtitle: Text(subtitle, style: const TextStyle(color: Color(0xFF8B7AB0), fontSize: 12)),
      trailing: const Icon(Icons.chevron_right_rounded, color: Color(0xFF8B7AB0)),
    );
  }
}
