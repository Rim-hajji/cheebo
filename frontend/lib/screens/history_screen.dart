import 'package:flutter/material.dart';
import 'dart:ui';
import '../services/api_service.dart';

// ─── Cheebo Brand Colors ─────────────────────────────────────────────
const kBgDark = Color(0xFF0D0820);
const kBgCard = Color(0xFF1A1232);
const kBgCardLight = Color(0xFF231A40);
const kPrimary = Color(0xFF7B56E2);
const kSecondary = Color(0xFF9A7BF2);
const kAccent = Color(0xFFC084FC);
const kTextMuted = Color(0xFF8B7AB0);

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen>
    with SingleTickerProviderStateMixin {
  List<Map<String, dynamic>> _history = [];
  List<Map<String, dynamic>> _filtered = [];
  bool _isLoading = true;
  String _filter = 'TOUT';
  late AnimationController _listController;

  @override
  void initState() {
    super.initState();
    _listController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _loadHistory();
  }

  @override
  void dispose() {
    _listController.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    final data = await ApiService.getHistory();
    if (mounted) {
      setState(() {
        _history = data;
        _filtered = data;
        _isLoading = false;
      });
      _listController.forward();
    }
  }

  void _applyFilter(String f) {
    setState(() {
      _filter = f;
      if (f == 'TOUT') {
        _filtered = _history;
      } else if (f == 'URGENCE') {
        _filtered = _history
            .where(
                (h) => ['CRITICAL', 'HIGH'].contains(h['urgency_label']))
            .toList();
      } else {
        _filtered = _history
            .where(
                (h) => ['LOW', 'MODERATE'].contains(h['urgency_label']))
            .toList();
      }
    });
  }

  Color _labelColor(String label) {
    if (label == 'CRITICAL') return const Color(0xFFEF4444);
    if (label == 'HIGH') return const Color(0xFFF97316);
    if (label == 'MODERATE') return const Color(0xFFFBBF24);
    return const Color(0xFF34D399);
  }

  IconData _labelIcon(String label) {
    if (label == 'CRITICAL' || label == 'HIGH') {
      return Icons.warning_amber_rounded;
    }
    if (label == 'MODERATE') return Icons.info_outline_rounded;
    return Icons.check_circle_outline_rounded;
  }

  String _labelText(String label) {
    switch (label) {
      case 'CRITICAL':
        return 'Critique';
      case 'HIGH':
        return 'Urgent';
      case 'MODERATE':
        return 'Modéré';
      default:
        return 'Faible';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBgDark,
      body: Stack(
        children: [
          // Ambient background
          Positioned.fill(
            child: CustomPaint(painter: _HistoryBackgroundPainter()),
          ),
          Column(
            children: [
              _buildHeader(),
              _buildFilterChips(),
              Expanded(child: _buildHistoryList()),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: EdgeInsets.only(top: MediaQuery.of(context).padding.top),
      decoration: BoxDecoration(
        color: kBgCard.withOpacity(0.85),
        border: const Border(
          bottom: BorderSide(color: Color(0xFF2D2050), width: 0.5),
        ),
      ),
      child: ClipRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Padding(
            padding:
                const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
            child: Row(
              children: [
                Container(
                  width: 38,
                  height: 38,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: kPrimary.withOpacity(0.12),
                    border: Border.all(color: kPrimary.withOpacity(0.25)),
                  ),
                  child: const Icon(
                    Icons.history_rounded,
                    color: kAccent,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 12),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Historique',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        letterSpacing: -0.3,
                      ),
                    ),
                    Text(
                      '${_history.length} consultation${_history.length > 1 ? 's' : ''}',
                      style: const TextStyle(
                        color: kTextMuted,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                const Spacer(),
                // Stats mini
                if (_history.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: kPrimary.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: kPrimary.withOpacity(0.2)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.pets_rounded,
                            color: kAccent, size: 14),
                        const SizedBox(width: 4),
                        Text(
                          '${_history.length}',
                          style: const TextStyle(
                            color: kAccent,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFilterChips() {
    final filters = [
      {'label': 'TOUT', 'icon': Icons.all_inclusive_rounded},
      {'label': 'URGENCE', 'icon': Icons.warning_amber_rounded},
      {'label': 'CONSEIL', 'icon': Icons.lightbulb_outline_rounded},
    ];

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
      child: Row(
        children: filters.map((f) {
          final label = f['label'] as String;
          final icon = f['icon'] as IconData;
          final selected = _filter == label;

          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: GestureDetector(
              onTap: () => _applyFilter(label),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 250),
                curve: Curves.easeOutCubic,
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
                decoration: BoxDecoration(
                  gradient: selected
                      ? const LinearGradient(
                          colors: [Color(0xFF8B5CF6), kPrimary])
                      : null,
                  color: selected ? null : kBgCard,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: selected
                        ? Colors.transparent
                        : const Color(0xFF2D2050),
                  ),
                  boxShadow: selected
                      ? [
                          BoxShadow(
                            color: kPrimary.withOpacity(0.3),
                            blurRadius: 10,
                            offset: const Offset(0, 3),
                          )
                        ]
                      : [],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      icon,
                      size: 14,
                      color: selected ? Colors.white : kTextMuted,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      label,
                      style: TextStyle(
                        color: selected ? Colors.white : kTextMuted,
                        fontWeight: FontWeight.w600,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildHistoryList() {
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 36,
              height: 36,
              child: CircularProgressIndicator(
                color: kPrimary,
                strokeWidth: 2.5,
                backgroundColor: kPrimary.withOpacity(0.15),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'Chargement...',
              style: TextStyle(
                color: kTextMuted,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      );
    }

    if (_filtered.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: kPrimary.withOpacity(0.08),
                border: Border.all(color: kPrimary.withOpacity(0.15)),
              ),
              child: const Center(
                child: Text('🐾', style: TextStyle(fontSize: 36)),
              ),
            ),
            const SizedBox(height: 20),
            Text(
              _filter != 'TOUT'
                  ? 'Aucun résultat pour ce filtre'
                  : 'Aucune consultation',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Les analyses apparaîtront ici',
              style: TextStyle(
                color: kTextMuted,
                fontSize: 13,
              ),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      itemCount: _filtered.length,
      itemBuilder: (context, index) {
        final item = _filtered[index];
        final date = DateTime.tryParse(item['date'] ?? '');
        final formattedDate = date != null
            ? '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')} à ${date.hour}h${date.minute.toString().padLeft(2, '0')}'
            : 'Date inconnue';
        final label = item['urgency_label'] ?? 'LOW';
        final color = _labelColor(label);

        return TweenAnimationBuilder<double>(
          tween: Tween(begin: 0.0, end: 1.0),
          duration: Duration(milliseconds: 400 + index * 60),
          curve: Curves.easeOutCubic,
          builder: (context, value, child) {
            return Transform.translate(
              offset: Offset(0, 20 * (1 - value)),
              child: Opacity(opacity: value, child: child),
            );
          },
          child: Dismissible(
            key: Key(item['text'] ?? '$index'),
            direction: DismissDirection.endToStart,
            background: Container(
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.only(right: 24),
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.transparent,
                    Colors.red.withOpacity(0.15),
                  ],
                ),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.delete_outline_rounded,
                      color: Colors.redAccent, size: 22),
                  const SizedBox(height: 4),
                  const Text(
                    'Supprimer',
                    style: TextStyle(
                      color: Colors.redAccent,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ),
            onDismissed: (_) {
              setState(() => _filtered.removeAt(index));
            },
            child: Container(
              margin: const EdgeInsets.only(bottom: 12),
              decoration: BoxDecoration(
                color: kBgCard,
                borderRadius: BorderRadius.circular(18),
                border: Border.all(color: color.withOpacity(0.12)),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.15),
                    blurRadius: 8,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    // Status icon with glow
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: color.withOpacity(0.1),
                        border:
                            Border.all(color: color.withOpacity(0.2)),
                        boxShadow: [
                          BoxShadow(
                            color: color.withOpacity(0.15),
                            blurRadius: 8,
                          ),
                        ],
                      ),
                      child: Icon(
                        _labelIcon(label),
                        color: color,
                        size: 22,
                      ),
                    ),
                    const SizedBox(width: 14),
                    // Content
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '"${item['text']}"',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                              height: 1.3,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Icon(
                                Icons.access_time_rounded,
                                size: 12,
                                color: kTextMuted.withOpacity(0.7),
                              ),
                              const SizedBox(width: 4),
                              Text(
                                formattedDate,
                                style: TextStyle(
                                  color: kTextMuted.withOpacity(0.7),
                                  fontSize: 11,
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 10),
                    // Label badge
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 5),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(20),
                        border:
                            Border.all(color: color.withOpacity(0.25)),
                      ),
                      child: Text(
                        _labelText(label),
                        style: TextStyle(
                          color: color,
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

// ─── Background Painter ──────────────────────────────────────────────
class _HistoryBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..shader = RadialGradient(
        center: Alignment.topCenter,
        radius: 1.2,
        colors: [
          kPrimary.withOpacity(0.04),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint);
  }

  @override
  bool shouldRepaint(_) => false;
}
