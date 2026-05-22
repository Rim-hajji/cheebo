import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';
import 'chat_screen.dart';

// ─── Brand Colors ─────────────────────────────────────────────────
const _kBg      = Color(0xFF0D0820);
const _kCard    = Color(0xFF1A1232);
const _kCardL   = Color(0xFF231A40);
const _kPrimary = Color(0xFF7B56E2);
const _kAccent  = Color(0xFFC084FC);
const _kMuted   = Color(0xFF8B7AB0);
const _kBody    = Color(0xFFD0C0E8);

const _urgencyColors = {
  'LOW'      : Color(0xFF34D399),
  'MODERATE' : Color(0xFFFBBF24),
  'HIGH'     : Color(0xFFF97316),
  'CRITICAL' : Color(0xFFEF4444),
};

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with TickerProviderStateMixin {
  // MongoDB stats
  int _totalConversations = 0;
  Map<String, int> _distRemote = {};
  List<Map<String, dynamic>> _recentRemote = [];
  // Local fallback
  List<Map<String, dynamic>> _localHistory = [];
  bool _loading = true;

  late AnimationController _ringController;
  late AnimationController _fadeController;
  late Animation<double> _ringAnim;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();

    _ringController = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 1800),
    );
    _fadeController = AnimationController(
      vsync: this, duration: const Duration(milliseconds: 900),
    );

    _ringAnim = CurvedAnimation(parent: _ringController, curve: Curves.easeOutCubic);
    _fadeAnim = CurvedAnimation(parent: _fadeController, curve: Curves.easeOut);

    _loadData();
  }

  @override
  void dispose() {
    _ringController.dispose();
    _fadeController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    // Run both in parallel — API stats + local history
    final results = await Future.wait([
      ApiService.getStats(),
      ApiService.getHistory(),
    ]);
    final stats       = results[0] as Map<String, dynamic>;
    final localHistory = results[1] as List<Map<String, dynamic>>;

    if (mounted) {
      setState(() {
        _loading = false;
        _localHistory = localHistory;
        if (stats.isNotEmpty) {
          _totalConversations = stats['total_conversations'] as int? ?? 0;
          final rawDist = stats['urgency_distribution'] as Map<String, dynamic>? ?? {};
          _distRemote = rawDist.map((k, v) => MapEntry(k, (v as num).toInt()));
          _recentRemote = (stats['recent_conversations'] as List? ?? [])
              .cast<Map<String, dynamic>>();
        }
      });
      _fadeController.forward();
      Future.delayed(const Duration(milliseconds: 300), _ringController.forward);
    }
  }

  // ── Computed stats — prefer MongoDB, fall back to local ──────────
  bool get _hasRemote => _totalConversations > 0 || _distRemote.isNotEmpty;

  int get _total => _hasRemote ? _totalConversations : _localHistory.length;

  Map<String, int> get _dist {
    if (_hasRemote) {
      return {
        'LOW'     : _distRemote['LOW']      ?? 0,
        'MODERATE': _distRemote['MODERATE'] ?? 0,
        'HIGH'    : _distRemote['HIGH']     ?? 0,
        'CRITICAL': _distRemote['CRITICAL'] ?? 0,
      };
    }
    final m = <String, int>{'LOW': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0};
    for (final h in _localHistory) {
      final key = h['urgency_label'] as String? ?? 'LOW';
      m[key] = (m[key] ?? 0) + 1;
    }
    return m;
  }

  double get _healthScore {
    if (_total == 0) return 1.0;
    final d = _dist;
    final weighted = (d['LOW']! * 1.0 + d['MODERATE']! * 0.6 +
                      d['HIGH']! * 0.2 + d['CRITICAL']! * 0.0) / _total;
    return weighted.clamp(0.0, 1.0);
  }

  String get _scoreLabel {
    final s = _healthScore;
    if (s >= 0.8) return 'Excellent';
    if (s >= 0.6) return 'Bon';
    if (s >= 0.4) return 'Modéré';
    return 'Attention';
  }

  Color get _scoreColor {
    final s = _healthScore;
    if (s >= 0.8) return _urgencyColors['LOW']!;
    if (s >= 0.6) return _urgencyColors['MODERATE']!;
    if (s >= 0.4) return _urgencyColors['HIGH']!;
    return _urgencyColors['CRITICAL']!;
  }

  String get _lastUrgency {
    if (_hasRemote && _recentRemote.isNotEmpty) {
      return _recentRemote.first['last_urgency'] as String? ?? 'N/A';
    }
    return _localHistory.isNotEmpty
        ? (_localHistory.first['urgency_label'] ?? 'N/A')
        : 'N/A';
  }

  double get _avgScore {
    if (_localHistory.isEmpty) return 0;
    final sum = _localHistory.fold<num>(0, (s, h) => s + (h['score'] ?? 0));
    return sum / _localHistory.length;
  }

  // Unified timeline items — remote preferred (title+session), else local (text+date)
  List<Map<String, dynamic>> get _recent {
    if (_hasRemote && _recentRemote.isNotEmpty) {
      return _recentRemote.take(7).map((r) => {
        'urgency_label': r['last_urgency'] ?? 'LOW',
        'text'        : r['title'] ?? '',
        'date'        : r['updated_at'] ?? '',
      }).toList();
    }
    return _localHistory.take(7).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _kBg,
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: _kPrimary))
          : RefreshIndicator(
              color: _kPrimary,
              backgroundColor: _kCard,
              onRefresh: _loadData,
              child: CustomScrollView(
                slivers: [
                  _buildAppBar(),
                  SliverPadding(
                    padding: const EdgeInsets.fromLTRB(20, 0, 20, 70),
                    sliver: SliverFadeTransition(
                      opacity: _fadeAnim,
                      sliver: SliverList(
                        delegate: SliverChildListDelegate([
                          const SizedBox(height: 24),
                          _buildHealthRing(),
                          const SizedBox(height: 28),
                          _buildStatsRow(),
                          const SizedBox(height: 24),
                          _buildSectionTitle('Dernières consultations', Icons.timeline_rounded),
                          const SizedBox(height: 12),
                          _buildTimeline(),
                          const SizedBox(height: 24),
                          _buildSectionTitle('Répartition des urgences', Icons.bar_chart_rounded),
                          const SizedBox(height: 12),
                          _buildUrgencyBars(),
                          const SizedBox(height: 24),
                          _buildQuickActions(context),
                        ]),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  // ── App Bar ──────────────────────────────────────────────────────
  Widget _buildAppBar() {
    final now = DateTime.now();
    final months = ['Jan','Fév','Mar','Avr','Mai','Jun','Jul','Aoû','Sep','Oct','Nov','Déc'];
    return SliverAppBar(
      expandedHeight: 80,
      floating: true,
      backgroundColor: _kBg,
      flexibleSpace: FlexibleSpaceBar(
        background: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF1A0F35), _kBg],
              begin: Alignment.topCenter, end: Alignment.bottomCenter,
            ),
          ),
          child: SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${now.day} ${months[now.month - 1]} ${now.year}',
                          style: const TextStyle(color: _kMuted, fontSize: 12, letterSpacing: 0.5),
                        ),
                        const SizedBox(height: 2),
                        const Text('Tableau de Bord',
                            style: TextStyle(color: Colors.white, fontSize: 22,
                                fontWeight: FontWeight.w800, letterSpacing: -0.5)),
                      ],
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: _kPrimary.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: _kPrimary.withOpacity(0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.pets, size: 14, color: _kAccent),
                        const SizedBox(width: 4),
                        Text('$_total analyses',
                            style: const TextStyle(color: _kAccent, fontSize: 12, fontWeight: FontWeight.w600)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ── Health Ring ──────────────────────────────────────────────────
  Widget _buildHealthRing() {
    return Center(
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outer glow
          Container(
            width: 220, height: 220,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(color: _scoreColor.withOpacity(0.15), blurRadius: 40, spreadRadius: 10),
              ],
            ),
          ),
          // Ring
          AnimatedBuilder(
            animation: _ringAnim,
            builder: (_, __) => CustomPaint(
              size: const Size(200, 200),
              painter: _HealthRingPainter(
                progress : _total == 0 ? 0 : _healthScore * _ringAnim.value,
                color    : _scoreColor,
                bgColor  : _kCard,
              ),
            ),
          ),
          // Center content
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AnimatedBuilder(
                animation: _ringAnim,
                builder: (_, __) => Text(
                  _total == 0
                      ? '–'
                      : '${(_healthScore * _ringAnim.value * 100).round()}%',
                  style: TextStyle(
                    color: _scoreColor,
                    fontSize: 42,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -1,
                  ),
                ),
              ),
              Text(_total == 0 ? 'Aucune donnée' : _scoreLabel,
                  style: const TextStyle(color: _kBody, fontSize: 14, fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              const Text('Indice de santé global',
                  style: TextStyle(color: _kMuted, fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }

  // ── Stats Row ────────────────────────────────────────────────────
  Widget _buildStatsRow() {
    return Row(
      children: [
        _statCard(Icons.bar_chart, 'Analyses', '$_total', _kPrimary),
        const SizedBox(width: 12),
        _statCard(Icons.priority_high_rounded, 'Dernière\nurgence', _lastUrgency,
            _urgencyColors[_lastUrgency] ?? _kMuted),
        const SizedBox(width: 12),
        _statCard(Icons.trending_up, 'Score\nmoyen', '${_avgScore.toStringAsFixed(1)}/10', _kAccent),
      ],
    );
  }

  Widget _statCard(IconData icon, String label, String value, Color accent) {
    return Expanded(
      child: ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 16),
            decoration: BoxDecoration(
              color: _kCard,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: accent.withOpacity(0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(icon, size: 20, color: accent),
                const SizedBox(height: 8),
                Text(value,
                    style: TextStyle(color: accent, fontSize: 16,
                        fontWeight: FontWeight.w800, letterSpacing: -0.3)),
                const SizedBox(height: 2),
                Text(label,
                    style: const TextStyle(color: _kMuted, fontSize: 10,
                        fontWeight: FontWeight.w500, height: 1.3)),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // ── Section Title ────────────────────────────────────────────────
  Widget _buildSectionTitle(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: _kAccent, size: 16),
        const SizedBox(width: 8),
        Text(title, style: const TextStyle(
            color: Colors.white, fontSize: 14, fontWeight: FontWeight.w700, letterSpacing: 0.2)),
      ],
    );
  }

  // ── Timeline ─────────────────────────────────────────────────────
  Widget _buildTimeline() {
    if (_recent.isEmpty) {
      return _emptyCard('Aucune consultation enregistrée');
    }
    return Container(
      decoration: BoxDecoration(
        color: _kCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _kPrimary.withOpacity(0.1)),
      ),
      child: Column(
        children: List.generate(_recent.length, (i) {
          final h     = _recent[i];
          final label = h['urgency_label'] as String? ?? 'LOW';
          final color = _urgencyColors[label] ?? _kMuted;
          final date  = DateTime.tryParse(h['date'] ?? '') ?? DateTime.now();
          final text  = (h['text'] as String?) ?? '';
          final isLast = i == _recent.length - 1;

          return IntrinsicHeight(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Timeline line + dot
                Padding(
                  padding: const EdgeInsets.only(left: 20),
                  child: Column(
                    children: [
                      const SizedBox(height: 18),
                      Container(width: 10, height: 10,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle, color: color,
                            boxShadow: [BoxShadow(color: color.withOpacity(0.4), blurRadius: 6)],
                          )),
                      if (!isLast)
                        Expanded(
                          child: Container(width: 1.5, color: _kPrimary.withOpacity(0.15)),
                        ),
                      if (isLast) const SizedBox(height: 16),
                    ],
                  ),
                ),
                const SizedBox(width: 14),
                // Content
                Expanded(
                  child: Padding(
                    padding: EdgeInsets.only(
                        top: 12, bottom: isLast ? 16 : 12, right: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: color.withOpacity(0.12),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(label,
                                  style: TextStyle(color: color, fontSize: 10,
                                      fontWeight: FontWeight.w700)),
                            ),
                            const Spacer(),
                            Text(
                              '${date.day}/${date.month} ${date.hour.toString().padLeft(2,'0')}:${date.minute.toString().padLeft(2,'0')}',
                              style: const TextStyle(color: _kMuted, fontSize: 10),
                            ),
                          ],
                        ),
                        const SizedBox(height: 5),
                        Text(
                          text.length > 60 ? '${text.substring(0, 60)}…' : text,
                          style: const TextStyle(color: _kBody, fontSize: 12, height: 1.4),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        }),
      ),
    );
  }

  // ── Urgency Bars ─────────────────────────────────────────────────
  Widget _buildUrgencyBars() {
    final dist   = _dist;
    final labels = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'];
    final icons  = [Icons.check_circle_rounded, Icons.warning_rounded, Icons.warning_amber_rounded, Icons.error_rounded];
    final names  = ['Bénin', 'Modéré', 'Élevé', 'Critique'];
    final maxVal = dist.values.fold<int>(1, (a, b) => b > a ? b : a);

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _kCard,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _kPrimary.withOpacity(0.1)),
      ),
      child: Column(
        children: List.generate(4, (i) {
          final key   = labels[i];
          final count = dist[key] ?? 0;
          final ratio = maxVal == 0 ? 0.0 : count / maxVal;
          final color = _urgencyColors[key]!;
          return Padding(
            padding: EdgeInsets.only(bottom: i < 3 ? 14 : 0),
            child: Row(
              children: [
                Icon(icons[i], size: 16, color: _urgencyColors[labels[i]]),
                const SizedBox(width: 8),
                SizedBox(width: 52,
                    child: Text(names[i],
                        style: const TextStyle(color: _kBody, fontSize: 11,
                            fontWeight: FontWeight.w500))),
                const SizedBox(width: 8),
                Expanded(
                  child: AnimatedBuilder(
                    animation: _ringAnim,
                    builder: (_, __) => ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: LinearProgressIndicator(
                        value   : ratio * _ringAnim.value,
                        minHeight: 8,
                        backgroundColor: _kCardL,
                        valueColor: AlwaysStoppedAnimation<Color>(color),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                SizedBox(width: 24,
                    child: Text('$count',
                        style: TextStyle(color: color, fontSize: 12,
                            fontWeight: FontWeight.w700),
                        textAlign: TextAlign.right)),
              ],
            ),
          );
        }),
      ),
    );
  }

  // ── Quick Actions ────────────────────────────────────────────────
  Widget _buildQuickActions(BuildContext context) {
    return Row(
      children: [
        Expanded(
          flex: 3,
          child: _actionCard(
            gradient: const LinearGradient(
              colors: [Color(0xFF7B56E2), Color(0xFF4B2DB0)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            icon: Icons.pets,
            title: 'Consulter Cheebo',
            subtitle: 'Décrire des symptômes',
            onTap: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => const ChatScreen()),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          flex: 2,
          child: _actionCard(
            gradient: const LinearGradient(
              colors: [Color(0xFF7B1A1A), Color(0xFF4A0E0E)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            icon: Icons.emergency_rounded,
            title: 'Urgence',
            subtitle: 'Vétérinaires 24/7',
            onTap: () => _showEmergencyVets(context),
          ),
        ),
      ],
    );
  }

  Widget _actionCard({
    required Gradient gradient,
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: gradient,
          borderRadius: BorderRadius.circular(18),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.25),
              blurRadius: 12, offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(icon, size: 28, color: Colors.white),
            const SizedBox(height: 10),
            Text(title, style: const TextStyle(
                color: Colors.white, fontSize: 13, fontWeight: FontWeight.w700)),
            const SizedBox(height: 2),
            Text(subtitle, style: TextStyle(
                color: Colors.white.withOpacity(0.65), fontSize: 10)),
          ],
        ),
      ),
    );
  }

  void _showEmergencyVets(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: _kCard,
      shape: const RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      builder: (_) => _EmergencyVetsSheet(),
    );
  }

  Widget _emptyCard(String msg) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
          color: _kCard, borderRadius: BorderRadius.circular(16)),
      child: Center(
        child: Text(msg, style: const TextStyle(color: _kMuted, fontSize: 13)),
      ),
    );
  }

  IconData _getUrgencyIcon(String level) {
    return switch(level) {
      'CRITICAL' => Icons.emergency_rounded,
      'HIGH' => Icons.priority_high_rounded,
      'MODERATE' => Icons.warning_amber_rounded,
      _ => Icons.check_circle_rounded,
    };
  }

  Future<void> _makePhoneCall(String phoneNumber) async {
    final Uri launchUri = Uri(scheme: 'tel', path: phoneNumber);
    if (await canLaunchUrl(launchUri)) {
      await launchUrl(launchUri);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Impossible de passer l\'appel')),
      );
    }
  }
}

// ── Emergency Vets Sheet (loads from API) ─────────────────────────
class _EmergencyVetsSheet extends StatefulWidget {
  @override
  State<_EmergencyVetsSheet> createState() => _EmergencyVetsSheetState();
}

class _EmergencyVetsSheetState extends State<_EmergencyVetsSheet> {
  List<Map<String, dynamic>> _vets = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final vets = await ApiService.getPartnerVets(emergencyOnly: false);
    if (mounted) setState(() { _vets = vets; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 36, height: 4,
              decoration: BoxDecoration(
                  color: _kMuted.withOpacity(0.4),
                  borderRadius: BorderRadius.circular(2)),
            ),
          ),
          const SizedBox(height: 16),
          const Text('🏥 Vétérinaires partenaires Cheebo',
              style: TextStyle(color: Colors.white, fontSize: 16,
                  fontWeight: FontWeight.w700)),
          const SizedBox(height: 16),
          if (_loading)
            const Center(child: Padding(
              padding: EdgeInsets.all(20),
              child: CircularProgressIndicator(color: _kPrimary),
            ))
          else if (_vets.isEmpty)
            const Text('Aucun vétérinaire disponible.',
                style: TextStyle(color: _kMuted))
          else
            ..._vets.map((v) {
              final isEmergency = v['emergency'] as bool? ?? false;
              final specs = (v['specialties'] as List?)?.join(' • ') ?? '';
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _vetTileWidget(
                  v['name'] as String? ?? '',
                  v['phone'] as String? ?? '',
                  specs.isEmpty ? (isEmergency ? "Urgences" : '') : specs,
                  isEmergency,
                ),
              );
            }),
        ],
      ),
    );
  }

  Widget _vetTileWidget(String name, String phone, String tag, bool isEmergency) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _kCardL,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: isEmergency
            ? Colors.red.withOpacity(0.25)
            : _kPrimary.withOpacity(0.15)),
      ),
      child: Row(
        children: [
          if (isEmergency)
            Container(
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.red.withOpacity(0.15),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Icon(Icons.emergency_rounded, size: 16, color: Colors.redAccent),
            ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(name, style: const TextStyle(
                    color: Colors.white, fontSize: 13, fontWeight: FontWeight.w600)),
                const SizedBox(height: 3),
                if (tag.isNotEmpty)
                  Text(tag, style: TextStyle(
                      color: isEmergency ? Colors.redAccent : _kMuted, fontSize: 11),
                      maxLines: 1, overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () {
              if (phone.isNotEmpty) {
                _makePhoneCall(phone);
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [_kAccent, _kPrimary]),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(phone,
                  style: const TextStyle(color: Colors.white, fontSize: 10,
                      fontWeight: FontWeight.w700)),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _makePhoneCall(String phoneNumber) async {
    final Uri launchUri = Uri(scheme: 'tel', path: phoneNumber);
    if (await canLaunchUrl(launchUri)) {
      await launchUrl(launchUri);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Impossible de passer l\'appel')),
      );
    }
  }
}

// ── Health Ring Painter ────────────────────────────────────────────
class _HealthRingPainter extends CustomPainter {
  final double progress;
  final Color color;
  final Color bgColor;

  const _HealthRingPainter({
    required this.progress,
    required this.color,
    required this.bgColor,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final cx = size.width / 2;
    final cy = size.height / 2;
    final r  = math.min(cx, cy) - 12;
    const stroke = 16.0;

    // Background track
    canvas.drawArc(
      Rect.fromCircle(center: Offset(cx, cy), radius: r),
      -math.pi / 2, 2 * math.pi, false,
      Paint()
        ..color    = bgColor
        ..style    = PaintingStyle.stroke
        ..strokeWidth = stroke
        ..strokeCap   = StrokeCap.round,
    );

    // Glow layer
    if (progress > 0) {
      canvas.drawArc(
        Rect.fromCircle(center: Offset(cx, cy), radius: r),
        -math.pi / 2, 2 * math.pi * progress, false,
        Paint()
          ..color    = color.withOpacity(0.25)
          ..style    = PaintingStyle.stroke
          ..strokeWidth = stroke + 8
          ..strokeCap   = StrokeCap.round
          ..maskFilter  = const MaskFilter.blur(BlurStyle.normal, 8),
      );
    }

    // Progress arc
    if (progress > 0) {
      final shader = SweepGradient(
        startAngle: -math.pi / 2,
        endAngle  : -math.pi / 2 + 2 * math.pi * progress,
        colors    : [color.withOpacity(0.7), color],
      ).createShader(Rect.fromCircle(center: Offset(cx, cy), radius: r));

      canvas.drawArc(
        Rect.fromCircle(center: Offset(cx, cy), radius: r),
        -math.pi / 2, 2 * math.pi * progress, false,
        Paint()
          ..shader     = shader
          ..style      = PaintingStyle.stroke
          ..strokeWidth= stroke
          ..strokeCap  = StrokeCap.round,
      );
    }

    // Tick marks
    final tickPaint = Paint()
      ..color      = Colors.white.withOpacity(0.06)
      ..strokeWidth= 1.5;
    for (int i = 0; i < 36; i++) {
      final angle  = -math.pi / 2 + (i * 2 * math.pi / 36);
      final inner  = r - stroke / 2 - 4;
      final outer  = r + stroke / 2 + 4;
      canvas.drawLine(
        Offset(cx + inner * math.cos(angle), cy + inner * math.sin(angle)),
        Offset(cx + outer * math.cos(angle), cy + outer * math.sin(angle)),
        tickPaint,
      );
    }
  }

  @override
  bool shouldRepaint(_HealthRingPainter old) =>
      old.progress != progress || old.color != color;
}

// ── Shell helper (used by action card to switch tab) ──────────────
class _DashboardShellState {}
