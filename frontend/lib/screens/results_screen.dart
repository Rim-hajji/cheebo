import 'package:flutter/material.dart';

const kBgDark = Color(0xFF120C24);
const kBgCard = Color(0xFF1E1535);
const kPrimary = Color(0xFF7B56E2);
const kSecondary = Color(0xFF9A7BF2);

class ResultsScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  const ResultsScreen({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    final analysis = data['analysis'] ?? {};
    final results = data['results'] ?? {};
    final symptoms = results['symptoms'] ?? {};
    final care = results['care'] ?? {};
    final urgencyInfo = results['urgency'] ?? {};

    final level = analysis['urgency_label'] ?? 'LOW';
    final isModerate = level == 'MODERATE';
    final sentimentScore = (analysis['sentiment_score'] ?? 50) as num;
    final List<dynamic> entities = analysis['entities'] ?? [];

    return Scaffold(
      backgroundColor: kBgDark,
      appBar: AppBar(
        backgroundColor: kBgCard,
        title: const Text('Analyse', style: TextStyle(fontWeight: FontWeight.bold)),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status Badge
            _buildStatusBadge(level, isModerate),
            const SizedBox(height: 16),

            // Recommendation delay
            if (urgencyInfo['recommandation_delai'] != null)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                decoration: BoxDecoration(
                  color: kBgCard,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF3D2E6E)),
                ),
                child: Text(
                  urgencyInfo['recommandation_delai'] ?? '',
                  style: const TextStyle(color: Color(0xFFB0A0CC), fontSize: 13, height: 1.4),
                  textAlign: TextAlign.center,
                ),
              ),
            const SizedBox(height: 20),

            // Vitality Widget
            _buildVitalityWidget(sentimentScore),
            const SizedBox(height: 20),

            // Entities chips
            if (entities.isNotEmpty) ...[
              const Text('Éléments détectés par l\'IA :', style: TextStyle(color: kSecondary, fontSize: 13, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: entities.map((e) {
                  final label = e['label'];
                  final Color chipBg = label == 'SYMPTOM' ? Colors.redAccent.withOpacity(0.15)
                      : (label == 'ANIMAL' ? Colors.blueAccent.withOpacity(0.15) : kPrimary.withOpacity(0.15));
                  final Color chipBorder = label == 'SYMPTOM' ? Colors.redAccent
                      : (label == 'ANIMAL' ? Colors.blueAccent : kPrimary);
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: chipBg,
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: chipBorder.withOpacity(0.4)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(label.toString().substring(0, 1), style: TextStyle(color: chipBorder, fontSize: 10, fontWeight: FontWeight.bold)),
                        const SizedBox(width: 6),
                        Text(e['text'], style: const TextStyle(color: Colors.white, fontSize: 13)),
                      ],
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),
            ],

            // Causas Potentielles
            if (symptoms['causes_potentielles'] != null && (symptoms['causes_potentielles'] as List).isNotEmpty)
              _buildCard(
                'Causes Potentielles',
                Icons.search_rounded,
                symptoms['causes_potentielles'],
                footer: symptoms['avertissement'],
                accentColor: Colors.orangeAccent,
              ),

            // Conseils
            if (care['conseils_maison_securises'] != null)
              _buildCard(
                'Conseils à la maison',
                Icons.home_rounded,
                care['conseils_maison_securises'],
                accentColor: Colors.greenAccent,
                isSafe: true,
              ),

            // Bouton retour
            const SizedBox(height: 8),
            OutlinedButton.icon(
              icon: const Icon(Icons.arrow_back_rounded),
              label: const Text('Nouvelle analyse'),
              style: OutlinedButton.styleFrom(
                foregroundColor: kSecondary,
                side: const BorderSide(color: Color(0xFF3D2E6E)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusBadge(String level, bool isModerate) {
    final color = isModerate ? Colors.orangeAccent : Colors.greenAccent;
    final icon = isModerate ? Icons.info_rounded : Icons.check_circle_rounded;
    final label = isModerate ? '⚠️ Attention Modérée' : '✅ Situation Bénigne';

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 16, horizontal: 20),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 32),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: TextStyle(color: color, fontWeight: FontWeight.bold, fontSize: 17)),
                const SizedBox(height: 2),
                Text('Criticité: $level', style: TextStyle(color: color.withOpacity(0.7), fontSize: 13)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildVitalityWidget(num sentimentScore) {
    final isCalm = sentimentScore > 50;
    final color = isCalm ? Colors.greenAccent : Colors.redAccent;
    final moodLabel = isCalm ? 'CALME • EN FORME' : 'STRESSÉ • INQUIET';
    final emoji = isCalm ? '😌' : '😰';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: kBgCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: kPrimary.withOpacity(0.3)),
        gradient: LinearGradient(
          colors: [const Color(0xFF1E1535), color.withOpacity(0.05)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Text(emoji, style: const TextStyle(fontSize: 28)),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('VITALITÉ', style: TextStyle(color: Color(0xFF9A7BF2), fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                        Text('${sentimentScore.toInt()}%', style: TextStyle(color: color, fontSize: 18, fontWeight: FontWeight.bold)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value: sentimentScore / 100.0,
                        backgroundColor: Colors.white10,
                        valueColor: AlwaysStoppedAnimation<Color>(color),
                        minHeight: 10,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(moodLabel, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 0.5)),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCard(String title, IconData icon, List<dynamic> items, {String? footer, Color accentColor = kPrimary, bool isSafe = false}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      decoration: BoxDecoration(
        color: kBgCard,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: accentColor.withOpacity(0.2)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(color: accentColor.withOpacity(0.12), borderRadius: BorderRadius.circular(10)),
                  child: Icon(icon, color: accentColor, size: 22),
                ),
                const SizedBox(width: 12),
                Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Colors.white)),
              ],
            ),
            const SizedBox(height: 16),
            ...items.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.arrow_right_rounded, color: accentColor, size: 22),
                  const SizedBox(width: 8),
                  Expanded(child: Text(item.toString(), style: const TextStyle(color: Color(0xFFD0C0E8), fontSize: 14, height: 1.5))),
                ],
              ),
            )),
            if (footer != null) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.redAccent.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(10),
                  border: Border(left: BorderSide(color: Colors.redAccent.withOpacity(0.5), width: 3)),
                ),
                child: Text(footer, style: const TextStyle(color: Color(0xFFB0A0CC), fontSize: 12, height: 1.4, fontStyle: FontStyle.italic)),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
