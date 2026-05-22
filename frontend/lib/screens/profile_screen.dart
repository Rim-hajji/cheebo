import 'package:flutter/material.dart';

const kBgDark = Color(0xFF120C24);
const kBgCard = Color(0xFF1E1535);
const kPrimary = Color(0xFF7B56E2);
const kSecondary = Color(0xFF9A7BF2);

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final TextEditingController _nameController = TextEditingController(text: 'Rex');
  final TextEditingController _ageController = TextEditingController(text: '3');
  final TextEditingController _breedController = TextEditingController(text: 'Golden Retriever');
  final TextEditingController _weightController = TextEditingController(text: '28');
  String _selectedAnimalType = 'Chien';
  String _selectedEmoji = '🐶';

  final List<String> _animalTypes = ['Chien', 'Chat', 'Oiseau', 'Rongeur', 'Reptile', 'Autre'];
  final Map<String, String> _emojiMap = {
    'Chien': '🐶', 'Chat': '🐱', 'Oiseau': '🐦', 'Rongeur': '🐹', 'Reptile': '🦎', 'Autre': '🐾',
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBgDark,
      appBar: AppBar(
        backgroundColor: kBgCard,
        title: const Text('Profil de l\'animal', style: TextStyle(fontWeight: FontWeight.bold)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(left: 24, right: 24, top: 24, bottom: 70),
        child: Column(
          children: [
            // Avatar
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(
                  colors: [Color(0xFF3D2B8E), kPrimary],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                boxShadow: [BoxShadow(color: kPrimary.withOpacity(0.4), blurRadius: 20)],
              ),
              child: Center(
                child: Text(_selectedEmoji, style: const TextStyle(fontSize: 48)),
              ),
            ),
            const SizedBox(height: 8),
            Text('Changer de compagnon', style: TextStyle(color: kSecondary, fontSize: 13, fontWeight: FontWeight.w600)),
            const SizedBox(height: 28),

            // Animal Type Row
            const Align(
              alignment: Alignment.centerLeft,
              child: Text('Type d\'animal', style: TextStyle(color: Color(0xFF9A7BF2), fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 0.8)),
            ),
            const SizedBox(height: 10),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _animalTypes.map((type) {
                  final selected = _selectedAnimalType == type;
                  return GestureDetector(
                    onTap: () => setState(() {
                      _selectedAnimalType = type;
                      _selectedEmoji = _emojiMap[type] ?? '🐾';
                    }),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      margin: const EdgeInsets.only(right: 10),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: selected ? kPrimary : kBgCard,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: selected ? kPrimary : const Color(0xFF3D2E6E)),
                      ),
                      child: Row(
                        children: [
                          Text(_emojiMap[type] ?? '🐾'),
                          const SizedBox(width: 6),
                          Text(type, style: TextStyle(color: selected ? Colors.white : const Color(0xFF9A7BF2), fontWeight: FontWeight.w600)),
                        ],
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 24),

            // Fields
            _buildField('Nom du compagnon', _nameController, Icons.badge_rounded),
            const SizedBox(height: 16),
            _buildField('Race', _breedController, Icons.search),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(child: _buildField('Âge (ans)', _ageController, Icons.cake_rounded, isNumber: true)),
                const SizedBox(width: 12),
                Expanded(child: _buildField('Poids (kg)', _weightController, Icons.monitor_weight_rounded, isNumber: true)),
              ],
            ),
            const SizedBox(height: 32),

            // Save Button
            SizedBox(
              width: double.infinity,
              height: 52,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.save_rounded),
                label: const Text('Sauvegarder le profil', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('${_selectedEmoji} Profil de ${_nameController.text} sauvegardé !'),
                      backgroundColor: kPrimary,
                      behavior: SnackBarBehavior.floating,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, IconData icon, {bool isNumber = false}) {
    return TextField(
      controller: controller,
      keyboardType: isNumber ? TextInputType.number : TextInputType.text,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: kSecondary, size: 20),
        labelStyle: const TextStyle(color: Color(0xFF8B7AB0)),
      ),
    );
  }
}
