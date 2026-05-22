import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'dart:ui';
import '../services/api_service.dart';
import '../services/notification_service.dart';
import '../theme/lux.dart';

const _categoryColors = {
  'Nutrition'        : kEmerald,
  'Vaccination'      : Color(0xFF60A5FA),
  'Hygiène'          : kRose,
  'Antiparasitaires' : Color(0xFFF97316),
  'Bien-être'        : kAccent,
  'Santé préventive' : Color(0xFF818CF8),
  'Comportement'     : Color(0xFFFCA5A5),
  'Urgences'         : kRed,
};

class ArticlesScreen extends StatefulWidget {
  const ArticlesScreen({super.key});

  @override
  State<ArticlesScreen> createState() => _ArticlesScreenState();
}

class _ArticlesScreenState extends State<ArticlesScreen>
    with SingleTickerProviderStateMixin {
  List<Map<String, dynamic>> _articles = [];
  List<Map<String, dynamic>> _filtered = [];
  bool _loading = true;
  String _selectedCategory = 'Tous';
  late AnimationController _fadeCtrl;
  late Animation<double> _fadeAnim;

  final List<String> _categories = [
    'Tous', 'Nutrition', 'Vaccination', 'Hygiène',
    'Antiparasitaires', 'Bien-être', 'Santé préventive',
    'Comportement', 'Urgences',
  ];

  @override
  void initState() {
    super.initState();
    _fadeCtrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _fadeAnim = CurvedAnimation(parent: _fadeCtrl, curve: Curves.easeOut);
    _load();
  }

  @override
  void dispose() {
    _fadeCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final data = await ApiService.getArticles();
    if (mounted) {
      setState(() { _articles = data; _filtered = data; _loading = false; });
      _fadeCtrl.forward();
    }
  }

  void _filter(String cat) {
    HapticFeedback.lightImpact();
    setState(() {
      _selectedCategory = cat;
      _filtered = cat == 'Tous'
          ? List.from(_articles)
          : _articles.where((a) => a['category'] == cat).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: Stack(children: [
        const LuxBackground(child: SizedBox.expand()),
        Column(children: [
          _buildHeader(context),
          _buildCategories(),
          Expanded(child: _buildList()),
        ]),
      ]),
    );
  }

  // ── 3D Glass Header ──────────────────────────────────────────────
  Widget _buildHeader(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
        child: Container(
          padding: EdgeInsets.only(
            top: MediaQuery.of(context).padding.top + 12,
            left: 20, right: 20, bottom: 14,
          ),
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [kBgCardL.withOpacity(0.96), kBgCard.withOpacity(0.9)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            border: Border(
              top: BorderSide(color: Colors.white.withOpacity(0.07), width: 0.6),
              bottom: BorderSide(color: Colors.black.withOpacity(0.4), width: 1.0),
            ),
            boxShadow: [
              BoxShadow(color: kPrimary.withOpacity(0.08), blurRadius: 20, offset: const Offset(0, 4)),
              BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10, offset: const Offset(0, 3)),
            ],
          ),
          child: Row(children: [
            // 3D icon
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: LinearGradient(colors: [kBgCardL, kBgCard]),
                border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                boxShadow: [
                  BoxShadow(color: kEmerald.withOpacity(0.25), blurRadius: 14),
                  BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 6, offset: const Offset(2, 3)),
                ],
              ),
              child: Center(child: ShaderMask(
                shaderCallback: (b) => gradEmerald.createShader(b),
                blendMode: BlendMode.srcIn,
                child: const Icon(Icons.health_and_safety_rounded, size: 22),
              )),
            ),
            const SizedBox(width: 14),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Bien-être Animal', style: TextStyle(
                  color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900, letterSpacing: -0.3)),
              Text('${_articles.length} articles curatés',
                  style: const TextStyle(color: Colors.white, fontSize: 11)),
            ]),
            const Spacer(),
            // 3D notification button
            GestureDetector(
              onTap: () async {
                HapticFeedback.lightImpact();
                await NotificationService.showNow();
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                    content: const Row(children: [
                      Icon(Icons.notifications_active_rounded, color: Colors.white, size: 16),
                      SizedBox(width: 8),
                      Text('Notification envoyée !'),
                    ]),
                    backgroundColor: kPrimary,
                    behavior: SnackBarBehavior.floating,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    duration: const Duration(seconds: 2),
                  ));
                }
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 13, vertical: 8),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [kPrimary.withOpacity(0.22), kBgCard],
                  ),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                  boxShadow: [
                    BoxShadow(color: kPrimary.withOpacity(0.2), blurRadius: 10),
                    BoxShadow(color: Colors.black.withOpacity(0.25), blurRadius: 6, offset: const Offset(1, 3)),
                  ],
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  ShaderMask(
                    shaderCallback: (b) => gradRose.createShader(b),
                    blendMode: BlendMode.srcIn,
                    child: const Icon(Icons.notifications_rounded, size: 15),
                  ),
                  const SizedBox(width: 6),
                  const Text('Notifier', style: TextStyle(color: kAccent2, fontSize: 12, fontWeight: FontWeight.w700)),
                ]),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  // ── Category chips ───────────────────────────────────────────────
  Widget _buildCategories() {
    return SizedBox(
      height: 52,
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        itemCount: _categories.length,
        itemBuilder: (_, i) {
          final cat      = _categories[i];
          final selected = _selectedCategory == cat;
          final color    = _categoryColors[cat] ?? kPrimary;
          return GestureDetector(
            onTap: () => _filter(cat),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 220),
              margin: const EdgeInsets.only(right: 8),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
              decoration: BoxDecoration(
                gradient: selected
                    ? LinearGradient(colors: [color.withOpacity(0.28), color.withOpacity(0.12)])
                    : LinearGradient(colors: [kBgCardL, kBgCard]),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: selected ? color.withOpacity(0.25) : Colors.white.withOpacity(0.08),
                  width: 0.7
                ),
                boxShadow: selected
                    ? [
                        BoxShadow(color: color.withOpacity(0.25), blurRadius: 12, offset: const Offset(0, 3)),
                        BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 6, offset: const Offset(1, 2)),
                      ]
                    : [BoxShadow(color: Colors.black.withOpacity(0.15), blurRadius: 4)],
              ),
              child: Text(cat, style: TextStyle(
                color: selected ? color : kMuted,
                fontSize: 12, fontWeight: FontWeight.w700,
              )),
            ),
          );
        },
      ),
    );
  }

  // ── Article List ─────────────────────────────────────────────────
  Widget _buildList() {
    if (_loading) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        SizedBox(
          width: 48, height: 48,
          child: CircularProgressIndicator(color: kRose, strokeWidth: 2,
              backgroundColor: kRose.withOpacity(0.1)),
        ),
        const SizedBox(height: 14),
        ShaderMask(
          shaderCallback: (b) => gradRose.createShader(b),
          blendMode: BlendMode.srcIn,
          child: const Text('Chargement…', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
        ),
      ]));
    }
    if (_filtered.isEmpty) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(colors: [kBgCardL, kBgCard]),
            border: Border.all(
              color: Colors.white.withOpacity(0.08),
              width: 0.7
            ),
          ),
          child: ShaderMask(
            shaderCallback: (b) => gradPrimary.createShader(b),
            blendMode: BlendMode.srcIn,
            child: const Icon(Icons.article_outlined, size: 40),
          ),
        ),
        const SizedBox(height: 14),
        const Text('Aucun article', style: TextStyle(color: kMuted, fontSize: 14)),
      ]));
    }
    return FadeTransition(
      opacity: _fadeAnim,
      child: ListView.builder(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(18, 8, 18, 120),
        itemCount: _filtered.length,
        itemBuilder: (_, i) => _buildCard(_filtered[i], i),
      ),
    );
  }

  // ── 3D Article Card ──────────────────────────────────────────────
  Widget _buildCard(Map<String, dynamic> article, int index) {
    final cat   = article['category'] as String? ?? 'Bien-être';
    final color = _categoryColors[cat] ?? kPrimary;
    final icon  = article['icon'] as String? ?? '🐾';

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: Duration(milliseconds: 300 + index * 50),
      curve: Curves.easeOutCubic,
      builder: (_, v, child) => Transform.translate(
        offset: Offset(0, 18 * (1 - v)),
        child: Opacity(opacity: v, child: child),
      ),
      child: Container(
        margin: const EdgeInsets.only(bottom: 14),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [kBgCardL, const Color(0xFF0E0923)],
            begin: Alignment.topLeft, end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.6),
          boxShadow: [
            BoxShadow(color: color.withOpacity(0.08), blurRadius: 18, offset: const Offset(0, 4)),
            BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 14, offset: const Offset(3, 6)),
            BoxShadow(color: Colors.white.withOpacity(0.03), offset: const Offset(-1, -1), blurRadius: 4),
          ],
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(22),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () { HapticFeedback.lightImpact(); _showArticleDetail(article); },
              splashColor: color.withOpacity(0.06),
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    // 3D emoji container
                    Container(
                      width: 48, height: 48,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [color.withOpacity(0.18), color.withOpacity(0.06)],
                          begin: Alignment.topLeft, end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                        boxShadow: [
                          BoxShadow(color: color.withOpacity(0.2), blurRadius: 10),
                          BoxShadow(color: Colors.black.withOpacity(0.25), blurRadius: 5, offset: const Offset(1, 2)),
                        ],
                      ),
                      child: Center(child: Text(icon, style: const TextStyle(fontSize: 22))),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [color.withOpacity(0.18), color.withOpacity(0.06)],
                            ),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(color: color.withOpacity(0.25), width: 0.5),
                          ),
                          child: Text(cat, style: TextStyle(
                              color: color, fontSize: 9.5, fontWeight: FontWeight.w800, letterSpacing: 0.3)),
                        ),
                        const SizedBox(height: 5),
                        Text(article['title'] as String? ?? '',
                            style: const TextStyle(color: kText, fontSize: 14,
                                fontWeight: FontWeight.w800, height: 1.2)),
                      ]),
                    ),
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [kBgCard, const Color(0xFF07041A)]),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.white.withOpacity(0.07), width: 0.6),
                      ),
                      child: Icon(Icons.chevron_right_rounded, color: kMuted, size: 18),
                    ),
                  ]),
                  const SizedBox(height: 12),
                  Text(article['summary'] as String? ?? '',
                      maxLines: 2, overflow: TextOverflow.ellipsis,
                      style: const TextStyle(color: kBody, fontSize: 12, height: 1.5)),
                  const SizedBox(height: 12),
                  // Tip section with gold-like border
                  Container(
                    padding: const EdgeInsets.all(11),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [color.withOpacity(0.1), color.withOpacity(0.03)],
                      ),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: color.withOpacity(0.2), width: 0.7),
                    ),
                    child: Row(children: [
                      Icon(Icons.lightbulb_outline_rounded, color: color, size: 13),
                      const SizedBox(width: 7),
                      Expanded(
                        child: Text(article['tip'] as String? ?? '',
                            maxLines: 2, overflow: TextOverflow.ellipsis,
                            style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w500, height: 1.3)),
                      ),
                    ]),
                  ),
                  const SizedBox(height: 10),
                  Row(children: [
                    Icon(Icons.verified_rounded, color: kMuted.withOpacity(0.6), size: 11),
                    const SizedBox(width: 5),
                    Text(article['source'] as String? ?? '',
                        style: const TextStyle(color: kMuted, fontSize: 10)),
                  ]),
                ]),
              ),
            ),
          ),
        ),
      ),
    );
  }

  // ── Article Detail Bottom Sheet ──────────────────────────────────
  void _showArticleDetail(Map<String, dynamic> article) {
    final cat   = article['category'] as String? ?? 'Bien-être';
    final color = _categoryColors[cat] ?? kPrimary;
    final icon  = article['icon'] as String? ?? '🐾';

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (_) => ClipRRect(
        borderRadius: const BorderRadius.vertical(top: Radius.circular(30)),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                colors: [kBgCardL.withOpacity(0.97), kBgCard.withOpacity(0.95)],
                begin: Alignment.topLeft, end: Alignment.bottomRight,
              ),
              borderRadius: const BorderRadius.vertical(top: Radius.circular(30)),
              border: Border.all(color: Colors.white.withOpacity(0.07), width: 0.6),
              boxShadow: [
                BoxShadow(color: color.withOpacity(0.08), blurRadius: 40, offset: const Offset(0, -8)),
              ],
            ),
            child: DraggableScrollableSheet(
              initialChildSize: 0.75,
              maxChildSize: 0.95,
              minChildSize: 0.4,
              expand: false,
              builder: (_, controller) => ListView(
                controller: controller,
                padding: const EdgeInsets.fromLTRB(22, 14, 22, 40),
                children: [
                  Center(
                    child: Container(
                      width: 44, height: 4,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [color, color.withOpacity(0.4)]),
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Container(
                      width: 56, height: 56,
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [color.withOpacity(0.2), color.withOpacity(0.06)],
                        ),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                        boxShadow: [BoxShadow(color: color.withOpacity(0.25), blurRadius: 14)],
                      ),
                      child: Center(child: Text(icon, style: const TextStyle(fontSize: 28))),
                    ),
                    const SizedBox(width: 14),
                    Expanded(
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(
                            gradient: LinearGradient(
                              colors: [color.withOpacity(0.2), color.withOpacity(0.08)],
                            ),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: color.withOpacity(0.3), width: 0.6),
                          ),
                          child: Text(cat, style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w800)),
                        ),
                        const SizedBox(height: 7),
                        Text(article['title'] as String? ?? '',
                            style: const TextStyle(color: kText, fontSize: 17,
                                fontWeight: FontWeight.w800, height: 1.2)),
                      ]),
                    ),
                  ]),
                  const SizedBox(height: 20),
                  const LuxDivider(),
                  const SizedBox(height: 18),
                  Text(article['summary'] as String? ?? '',
                      style: const TextStyle(color: kBody, fontSize: 14, height: 1.65)),
                  const SizedBox(height: 18),
                  // Tip card
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [color.withOpacity(0.12), color.withOpacity(0.04)],
                      ),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: color.withOpacity(0.2), width: 0.7),
                      boxShadow: [BoxShadow(color: color.withOpacity(0.1), blurRadius: 12)],
                    ),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Row(children: [
                        Icon(Icons.lightbulb_rounded, color: color, size: 15),
                        const SizedBox(width: 8),
                        Text('Conseil pratique', style: TextStyle(
                            color: color, fontSize: 12, fontWeight: FontWeight.w800)),
                      ]),
                      const SizedBox(height: 10),
                      Text(article['tip'] as String? ?? '',
                          style: TextStyle(color: color, fontSize: 13, height: 1.55)),
                    ]),
                  ),
                  const SizedBox(height: 16),
                  Row(children: [
                    Icon(Icons.verified_rounded, color: kMuted.withOpacity(0.6), size: 13),
                    const SizedBox(width: 6),
                    Text('Source : ${article['source'] ?? ''}',
                        style: const TextStyle(color: kMuted, fontSize: 11, fontStyle: FontStyle.italic)),
                  ]),
                  if ((article['url'] as String?)?.isNotEmpty == true) ...[
                    const SizedBox(height: 22),
                    GestureDetector(
                      onTap: () async {
                        HapticFeedback.lightImpact();
                        final uri = Uri.tryParse(article['url'] as String);
                        if (uri != null && await canLaunchUrl(uri)) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      },
                      child: Container(
                        width: double.infinity,
                        padding: const EdgeInsets.symmetric(vertical: 15),
                        decoration: BoxDecoration(
                          gradient: LinearGradient(
                            colors: [color.withOpacity(0.8), color],
                            begin: Alignment.topLeft, end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(color: color.withOpacity(0.2), width: 0.8),
                          boxShadow: [
                            BoxShadow(color: color.withOpacity(0.45), blurRadius: 20, offset: const Offset(0, 5)),
                            BoxShadow(color: Colors.black.withOpacity(0.35), blurRadius: 10, offset: const Offset(2, 5)),
                          ],
                        ),
                        child: Row(mainAxisAlignment: MainAxisAlignment.center, children: const [
                          Icon(Icons.open_in_new_rounded, color: Colors.white, size: 16),
                          SizedBox(width: 8),
                          Text("Lire l'article complet",
                              style: TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w800)),
                        ]),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
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
