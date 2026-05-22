import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/medication.dart';
import '../services/medication_service.dart';
import '../theme/lux.dart';

class MedicationsScreen extends StatefulWidget {
  const MedicationsScreen({super.key});

  @override
  State<MedicationsScreen> createState() => _MedicationsScreenState();
}

class _MedicationsScreenState extends State<MedicationsScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabCtrl;

  List<Medication> _meds     = [];
  List<Medication> _history  = [];
  bool _loading     = true;
  bool _histLoading = true;
  bool _isScanning  = false;

  @override
  void initState() {
    super.initState();
    _tabCtrl = TabController(length: 2, vsync: this);
    _tabCtrl.addListener(() => setState(() {}));
    _load();
    _loadHistory();
  }

  @override
  void dispose() {
    _tabCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final meds = await MedicationService.loadAll();
    if (mounted) setState(() { _meds = meds; _loading = false; });
  }

  Future<void> _loadHistory() async {
    final h = await MedicationService.loadHistory();
    if (mounted) setState(() { _history = h; _histLoading = false; });
  }

  Future<void> _delete(Medication med) async {
    setState(() => _meds.removeWhere((m) => m.id == med.id));
    await MedicationService.delete(med);
  }

  Future<void> _toggle(Medication med) async {
    await MedicationService.toggleActive(med);
    _load();
  }

  Future<void> _complete(Medication med) async {
    setState(() => _meds.removeWhere((m) => m.id == med.id));
    await MedicationService.complete(med);
    _loadHistory();
  }

  // ── OCR flow ─────────────────────────────────────────────────────
  Future<void> _scanAndAdd() async {
    Navigator.pop(context);
    final picker = ImagePicker();
    final img = await picker.pickImage(source: ImageSource.camera, imageQuality: 90);
    if (img == null) return;

    setState(() => _isScanning = true);
    try {
      final recognizer = TextRecognizer(script: TextRecognitionScript.latin);
      final result     = await recognizer.processImage(InputImage.fromFilePath(img.path));
      await recognizer.close();

      final parsed = MedicationService.parseMedName(result.text);
      if (!mounted) return;
      setState(() => _isScanning = false);

      if (parsed['isDanger'] == true) {
        _showDangerAlert(
            name: parsed['name'] as String, message: parsed['dangerMsg'] as String);
        return;
      }

      _showMedForm(
        prefillName         : parsed['name']          as String?,
        prefillDosage       : parsed['dosage']        as String?,
        prefillFreqLabel    : parsed['frequencyLabel'] as String?,
        prefillIntervalHours: parsed['intervalHours'] as int?,
        ocrFound            : parsed['fromDb'] == true,
        isUnknownMed        : parsed['fromDb'] == false,
      );
    } catch (_) {
      if (mounted) { setState(() => _isScanning = false); _showMedForm(); }
    }
  }

  // ── Danger alert ─────────────────────────────────────────────────
  void _showDangerAlert({required String name, required String message}) {
    showDialog(
      context: context,
      builder: (_) => Dialog(
        backgroundColor: Colors.transparent,
        child: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [kBg.withAlpha(200), kBgCard],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
            boxShadow: [
              BoxShadow(color: kRed.withOpacity(0.2), blurRadius: 30, offset: const Offset(0, 8)),
              BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 20, offset: const Offset(4, 10)),
            ],
          ),
          padding: const EdgeInsets.all(22),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start,
              children: [
            Row(children: [
              Container(
                width: 44, height: 44,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                      colors: [kRed.withOpacity(0.2), kRed.withOpacity(0.06)]),
                  border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                  boxShadow: [BoxShadow(color: kRed.withOpacity(0.4), blurRadius: 14)],
                ),
                child: const Center(child: Text('⚠️', style: TextStyle(fontSize: 20))),
              ),
              const SizedBox(width: 12),
              Expanded(child: Text(name,
                  style: const TextStyle(color: kText, fontSize: 16, fontWeight: FontWeight.w900))),
            ]),
            const SizedBox(height: 18),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                    colors: [kRed.withOpacity(0.1), kRed.withOpacity(0.03)]),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.white.withOpacity(0.06), width: 0.6),
              ),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Icon(Icons.dangerous_rounded, color: kRed, size: 16),
                const SizedBox(width: 10),
                Expanded(child: Text(message,
                    style: const TextStyle(
                        color: Color(0xFFFFB3B3), fontSize: 13, height: 1.55))),
              ]),
            ),
            const SizedBox(height: 14),
            const Text(
                'Ce médicament est conçu pour les humains.\nConsultez un vétérinaire avant tout usage.',
                style: TextStyle(color: kMuted, fontSize: 12, height: 1.5)),
            const SizedBox(height: 20),
            Align(
              alignment: Alignment.centerRight,
              child: GestureDetector(
                onTap: () => Navigator.pop(context),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  decoration: BoxDecoration(
                    gradient: gradPrimary,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white.withOpacity(0.12), width: 0.7),
                    boxShadow: [
                      BoxShadow(color: kPrimary.withOpacity(0.4), blurRadius: 12,
                          offset: const Offset(0, 3))
                    ],
                  ),
                  child: const Text('Compris',
                      style: TextStyle(
                          color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
                ),
              ),
            ),
          ]),
        ),
      ),
    );
  }

  // ── Add sheet ─────────────────────────────────────────────────────
  void _showAddSheet() {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
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
              border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
              boxShadow: [
                BoxShadow(color: kPrimary.withOpacity(0.08), blurRadius: 40,
                    offset: const Offset(0, -8))
              ],
            ),
            padding: const EdgeInsets.fromLTRB(22, 14, 22, 40),
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                Center(child: Container(
                  width: 44, height: 4,
                  decoration: BoxDecoration(
                      gradient: gradPrimary, borderRadius: BorderRadius.circular(2)),
                )),
                const SizedBox(height: 20),
                ShaderMask(
                  shaderCallback: (b) => gradPrimary.createShader(b),
                  blendMode: BlendMode.srcIn,
                  child: const Text('Ajouter un traitement',
                      style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
                ),
                const SizedBox(height: 4),
                const Text('Scanner la boîte ou saisir manuellement',
                    style: TextStyle(color: kMuted, fontSize: 12)),
                const SizedBox(height: 24),
                _addOption('📷', kAccent, 'Scanner la boîte',
                    'ML Kit OCR — détection automatique du médicament', _scanAndAdd),
                const SizedBox(height: 12),
                _addOption('✏️', kEmerald, 'Saisie manuelle',
                    'Remplir le formulaire manuellement',
                    () { Navigator.pop(context); _showMedForm(); }),
              ]),
            ),
          ),
        ),
      ),
    );
  }

  Widget _addOption(String emoji, Color color, String title, String subtitle,
      VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: LinearGradient(
              colors: [color.withOpacity(0.1), color.withOpacity(0.03)]),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
          boxShadow: [
            BoxShadow(color: color.withOpacity(0.12), blurRadius: 12),
            BoxShadow(color: Colors.black.withOpacity(0.25), blurRadius: 8,
                offset: const Offset(2, 3)),
          ],
        ),
        child: Row(children: [
          Container(
            width: 48, height: 48,
            decoration: BoxDecoration(
              gradient: LinearGradient(
                  colors: [color.withOpacity(0.2), color.withOpacity(0.06)]),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
              boxShadow: [BoxShadow(color: color.withOpacity(0.2), blurRadius: 8)],
            ),
            child: Center(child: Text(emoji, style: const TextStyle(fontSize: 22))),
          ),
          const SizedBox(width: 14),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title,
                style: const TextStyle(
                    color: kText, fontSize: 14, fontWeight: FontWeight.w800)),
            const SizedBox(height: 3),
            Text(subtitle, style: const TextStyle(color: kMuted, fontSize: 11)),
          ])),
          Container(
            padding: const EdgeInsets.all(7),
            decoration: BoxDecoration(
              color: color.withOpacity(0.12),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: color.withOpacity(0.25), width: 0.5),
            ),
            child: Icon(Icons.arrow_forward_ios_rounded, color: color, size: 12),
          ),
        ]),
      ),
    );
  }

  void _showMedForm({
    String? prefillName, String? prefillDosage, String? prefillFreqLabel,
    int? prefillIntervalHours, bool ocrFound = false, bool isUnknownMed = false,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (ctx) => _MedFormSheet(
        prefillName         : prefillName,
        prefillDosage       : prefillDosage,
        prefillFreqLabel    : prefillFreqLabel,
        prefillIntervalHours: prefillIntervalHours,
        ocrFound            : ocrFound,
        isUnknownMed        : isUnknownMed,
        onSave: (med) async { await MedicationService.add(med); if (mounted) _load(); },
      ),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: kBg,
      body: Stack(children: [
        const LuxBackground(child: SizedBox.expand()),
        Padding(
          padding: const EdgeInsets.only(bottom: 70),
          child: Column(children: [
            _buildHeader(context),
            _buildTabBar(),
            Expanded(child: TabBarView(
              controller: _tabCtrl,
              children: [_buildActiveBody(), _buildHistoryBody()],
            )),
          ]),
        ),
        if (_isScanning) _buildScanOverlay(),
      ]),
      floatingActionButton: _tabCtrl.index == 0 ? _buildFab() : null,
    );
  }

  Widget _buildFab() {
    return GestureDetector(
      onTap: () { HapticFeedback.lightImpact(); _showAddSheet(); },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF9D5CF6), Color(0xFF7C3AED)],
            begin: Alignment.topLeft, end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(color: const Color(0xFF7C3AED).withOpacity(0.5),
                blurRadius: 22, offset: const Offset(0, 6)),
            BoxShadow(color: Colors.black.withOpacity(0.45), blurRadius: 14,
                offset: const Offset(3, 8)),
          ],
        ),
        child: const Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(Icons.add_rounded, color: Colors.white, size: 20),
          SizedBox(width: 8),
          Text('Ajouter',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 14)),
        ]),
      ),
    );
  }

  Widget _buildTabBar() {
    return Container(
      margin: const EdgeInsets.fromLTRB(18, 12, 18, 0),
      decoration: BoxDecoration(
        color: kBgCard,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withOpacity(0.07), width: 0.6),
      ),
      child: TabBar(
        controller: _tabCtrl,
        tabs: const [Tab(text: 'Actifs'), Tab(text: 'Historique')],
        labelStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
        unselectedLabelStyle:
            const TextStyle(fontWeight: FontWeight.w500, fontSize: 13),
        labelColor: Colors.white,
        unselectedLabelColor: kMuted,
        indicator: BoxDecoration(
          gradient: gradPrimary,
          borderRadius: BorderRadius.circular(11),
        ),
        indicatorSize: TabBarIndicatorSize.tab,
        dividerColor: Colors.transparent,
        padding: const EdgeInsets.all(4),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    final active  = _meds.where((m) => m.isActive).length;
    final overdue = _meds
        .where((m) => m.isActive && m.nextDose.isBefore(DateTime.now()))
        .length;

    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
        child: Container(
          padding: EdgeInsets.only(
              top: MediaQuery.of(context).padding.top + 12,
              left: 20, right: 20, bottom: 14),
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
              BoxShadow(color: kPrimary.withOpacity(0.08), blurRadius: 20,
                  offset: const Offset(0, 4)),
            ],
          ),
          child: Row(children: [
            Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const LinearGradient(colors: [kBgCardL, kBgCard]),
                border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                boxShadow: [
                  BoxShadow(color: kPrimary.withOpacity(0.25), blurRadius: 12),
                  BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 6,
                      offset: const Offset(2, 3)),
                ],
              ),
              child: const Center(child: Text('💊', style: TextStyle(fontSize: 20))),
            ),
            const SizedBox(width: 14),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Pilulier', style: TextStyle(
                  fontSize: 20, fontWeight: FontWeight.w900,
                  letterSpacing: -0.3, color: Colors.white)),
              Text(
                '$active actif${active != 1 ? 's' : ''}'
                '${overdue > 0 ? ' · $overdue en retard' : ''}',
                style: TextStyle(
                    color: overdue > 0 ? kRed : kMuted,
                    fontSize: 11,
                    fontWeight: overdue > 0 ? FontWeight.w700 : FontWeight.w500),
              ),
            ]),
            const Spacer(),
            if (_meds.isNotEmpty)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 7),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                      colors: [kPrimary.withOpacity(0.2), kBgCard]),
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
                  boxShadow: [
                    BoxShadow(color: kPrimary.withOpacity(0.18), blurRadius: 10)
                  ],
                ),
                child: Text(
                    '${_meds.length} traitement${_meds.length != 1 ? 's' : ''}',
                    style: const TextStyle(
                        color: kAccent2, fontSize: 11, fontWeight: FontWeight.w700)),
              ),
          ]),
        ),
      ),
    );
  }

  // ── Tab bodies ────────────────────────────────────────────────────

  Widget _buildActiveBody() {
    if (_loading) return _buildLoader();
    if (_meds.isEmpty) return _buildEmptyState();
    return ListView.builder(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 120),
      itemCount: _meds.length,
      itemBuilder: (_, i) => TweenAnimationBuilder<double>(
        tween: Tween(begin: 0.0, end: 1.0),
        duration: Duration(milliseconds: 300 + i * 50),
        curve: Curves.easeOutCubic,
        builder: (_, v, child) => Transform.translate(
            offset: Offset(0, 20 * (1 - v)), child: Opacity(opacity: v, child: child)),
        child: _buildMedCard(_meds[i]),
      ),
    );
  }

  Widget _buildHistoryBody() {
    if (_histLoading) return _buildLoader();
    if (_history.isEmpty) return _buildEmptyHistory();
    return ListView.builder(
      physics: const BouncingScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(18, 14, 18, 120),
      itemCount: _history.length,
      itemBuilder: (_, i) => TweenAnimationBuilder<double>(
        tween: Tween(begin: 0.0, end: 1.0),
        duration: Duration(milliseconds: 300 + i * 50),
        curve: Curves.easeOutCubic,
        builder: (_, v, child) => Transform.translate(
            offset: Offset(0, 20 * (1 - v)), child: Opacity(opacity: v, child: child)),
        child: _buildHistoryCard(_history[i]),
      ),
    );
  }

  Widget _buildLoader() {
    return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
      SizedBox(
          width: 48, height: 48,
          child: CircularProgressIndicator(
              color: Colors.white, strokeWidth: 2,
              backgroundColor: Colors.white.withOpacity(0.1))),
      const SizedBox(height: 14),
      const Text('Chargement…',
          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: Colors.white)),
    ]));
  }

  Widget _buildEmptyState() {
    return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Container(
        width: 96, height: 96,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: const Color(0xFF2A1F4A),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 16,
                offset: const Offset(4, 6))
          ],
        ),
        child: const Center(child: Text('💊', style: TextStyle(fontSize: 44))),
      ),
      const SizedBox(height: 32),
      const Text('Aucun traitement actif',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: kText)),
      const SizedBox(height: 12),
      const Text('Ajoutez un traitement pour suivre\nles médicaments de votre animal',
          style: TextStyle(color: kMuted, fontSize: 13, height: 1.6),
          textAlign: TextAlign.center),
      const SizedBox(height: 36),
      GestureDetector(
        onTap: _showAddSheet,
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 13),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF9D5CF6), Color(0xFF7C3AED)],
              begin: Alignment.topLeft, end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(16),
            boxShadow: [
              BoxShadow(color: const Color(0xFF7C3AED).withOpacity(0.4),
                  blurRadius: 20, offset: const Offset(0, 6)),
              BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10,
                  offset: const Offset(2, 4)),
            ],
          ),
          child: const Row(mainAxisSize: MainAxisSize.min, children: [
            Icon(Icons.add_rounded, color: Colors.white, size: 18),
            SizedBox(width: 6),
            Text('Ajouter un traitement',
                style: TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w800, fontSize: 13)),
          ]),
        ),
      ),
    ]));
  }

  Widget _buildEmptyHistory() {
    return Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Container(
        width: 80, height: 80,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: kEmerald.withOpacity(0.06),
          border: Border.all(color: kEmerald.withOpacity(0.15), width: 0.8),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 16,
                offset: const Offset(4, 6))
          ],
        ),
        child: const Center(child: Text('📋', style: TextStyle(fontSize: 36))),
      ),
      const SizedBox(height: 28),
      const Text('Aucun historique',
          style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: kText)),
      const SizedBox(height: 10),
      const Text('Les traitements terminés\napparaîtront ici',
          style: TextStyle(color: kMuted, fontSize: 13, height: 1.6),
          textAlign: TextAlign.center),
    ]));
  }

  // ── Med card (actifs) ─────────────────────────────────────────────
  Widget _buildMedCard(Medication med) {
    final now      = DateTime.now();
    final isOver   = med.isActive && med.nextDose.isBefore(now);
    final barColor = !med.isActive ? kMuted : isOver ? kRed : kEmerald;

    final diff    = med.nextDose.difference(now);
    final timeStr = !med.isActive
        ? 'Inactif'
        : isOver ? 'En retard !'
        : diff.inDays > 0
            ? 'Dans ${diff.inDays}j ${diff.inHours.remainder(24)}h'
            : diff.inHours > 0
                ? 'Dans ${diff.inHours}h${diff.inMinutes.remainder(60).toString().padLeft(2, '0')}'
                : 'Dans ${diff.inMinutes}min';

    return Dismissible(
      key: Key(med.id),
      direction: DismissDirection.horizontal,
      // Glisser → droite = marquer terminé (vert)
      background: Container(
        alignment: Alignment.centerLeft,
        padding: const EdgeInsets.only(left: 24),
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
              colors: [kEmerald.withOpacity(0.15), Colors.transparent]),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                  colors: [kEmerald.withOpacity(0.25), kEmerald.withOpacity(0.08)]),
              border: Border.all(color: kEmerald.withOpacity(0.3), width: 0.6),
            ),
            child: const Icon(Icons.check_rounded, color: kEmerald, size: 18),
          ),
          const SizedBox(height: 4),
          const Text('Terminé',
              style: TextStyle(color: kEmerald, fontSize: 10, fontWeight: FontWeight.w700)),
        ]),
      ),
      // Glisser → gauche = supprimer (rouge)
      secondaryBackground: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 24),
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          gradient: LinearGradient(
              colors: [Colors.transparent, kRed.withOpacity(0.15)]),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                  colors: [kRed.withOpacity(0.2), kRed.withOpacity(0.08)]),
              border: Border.all(color: kRed.withOpacity(0.3), width: 0.6),
            ),
            child: const Icon(Icons.delete_rounded, color: kRed, size: 18),
          ),
          const SizedBox(height: 4),
          const Text('Supprimer',
              style: TextStyle(color: kRed, fontSize: 10, fontWeight: FontWeight.w700)),
        ]),
      ),
      onDismissed: (dir) {
        if (dir == DismissDirection.startToEnd) {
          _complete(med);
        } else {
          _delete(med);
        }
      },
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [kBgCardL, kBg],
            begin: Alignment.topLeft, end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
          boxShadow: [
            BoxShadow(color: barColor.withOpacity(0.1), blurRadius: 16,
                offset: const Offset(0, 3)),
            BoxShadow(color: Colors.black.withOpacity(0.4), blurRadius: 14,
                offset: const Offset(3, 5)),
            BoxShadow(color: Colors.white.withOpacity(0.03),
                offset: const Offset(-1, -1), blurRadius: 4),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              const Text('💊', style: TextStyle(fontSize: 18)),
              const SizedBox(width: 8),
              Expanded(child: Text(med.name,
                  style: const TextStyle(
                      color: kText, fontSize: 14, fontWeight: FontWeight.w800))),
              GestureDetector(
                onTap: () { HapticFeedback.lightImpact(); _toggle(med); },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 220),
                  width: 44, height: 25,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(13),
                    gradient: med.isActive
                        ? LinearGradient(colors: [
                            kEmerald.withOpacity(0.25),
                            kEmerald.withOpacity(0.1)
                          ])
                        : const LinearGradient(colors: [kBgCard, kBg]),
                    border: Border.all(
                        color: Colors.white
                            .withOpacity(med.isActive ? 0.10 : 0.07),
                        width: med.isActive ? 0.7 : 0.6),
                    boxShadow: [
                      if (med.isActive)
                        BoxShadow(
                            color: kEmerald.withOpacity(0.25), blurRadius: 8),
                    ],
                  ),
                  child: AnimatedAlign(
                    duration: const Duration(milliseconds: 220),
                    alignment: med.isActive
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Container(
                      width: 19, height: 19,
                      margin: const EdgeInsets.symmetric(horizontal: 3),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: med.isActive
                            ? LinearGradient(colors: [
                                Colors.white.withOpacity(0.9),
                                kEmerald
                              ])
                            : LinearGradient(colors: [
                                kMuted.withOpacity(0.6),
                                kMuted
                              ]),
                        boxShadow: [
                          BoxShadow(
                              color: (med.isActive ? kEmerald : kMuted)
                                  .withOpacity(0.4),
                              blurRadius: 5)
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ]),
            const SizedBox(height: 6),
            Text(med.dosage,
                style: const TextStyle(color: kBody, fontSize: 12, height: 1.3)),
            const SizedBox(height: 10),
            Row(children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [
                    kPrimary.withOpacity(0.18),
                    kPrimary.withOpacity(0.06)
                  ]),
                  borderRadius: BorderRadius.circular(8),
                  border:
                      Border.all(color: Colors.white.withOpacity(0.07), width: 0.6),
                ),
                child: Text(med.frequencyLabel,
                    style: const TextStyle(
                        color: kAccent2, fontSize: 10, fontWeight: FontWeight.w700)),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [
                    barColor.withOpacity(0.15),
                    barColor.withOpacity(0.04)
                  ]),
                  borderRadius: BorderRadius.circular(8),
                  border:
                      Border.all(color: barColor.withOpacity(0.25), width: 0.5),
                ),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  Icon(
                      isOver
                          ? Icons.warning_amber_rounded
                          : Icons.access_time_rounded,
                      color: barColor,
                      size: 11),
                  const SizedBox(width: 4),
                  Text(timeStr,
                      style: TextStyle(
                          color: barColor,
                          fontSize: 11,
                          fontWeight: FontWeight.w700)),
                ]),
              ),
            ]),
            if (med.notes != null) ...[
              const SizedBox(height: 8),
              Text('📝 ${med.notes}',
                  style: const TextStyle(color: kMuted, fontSize: 11)),
            ],
          ]),
        ),
      ),
    );
  }

  // ── History card ──────────────────────────────────────────────────
  Widget _buildHistoryCard(Medication med) {
    final c = med.completedAt;
    final dateStr = c != null
        ? '${c.day.toString().padLeft(2, '0')}/${c.month.toString().padLeft(2, '0')}/${c.year}'
        : '—';

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [kBgCardL.withOpacity(0.75), kBg.withOpacity(0.75)],
          begin: Alignment.topLeft, end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withOpacity(0.06), width: 0.6),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 10,
              offset: const Offset(2, 4))
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(colors: [
                kEmerald.withOpacity(0.15),
                kEmerald.withOpacity(0.04)
              ]),
              border: Border.all(color: kEmerald.withOpacity(0.25), width: 0.6),
            ),
            child: const Center(child: Text('✅', style: TextStyle(fontSize: 20))),
          ),
          const SizedBox(width: 12),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(med.name,
                style: const TextStyle(
                    color: kText, fontSize: 13, fontWeight: FontWeight.w800)),
            const SizedBox(height: 2),
            Text(med.dosage,
                style: const TextStyle(color: kBody, fontSize: 11)),
            const SizedBox(height: 6),
            Row(children: [
              const Icon(Icons.check_circle_outline_rounded,
                  color: kEmerald, size: 11),
              const SizedBox(width: 4),
              Text('Terminé le $dateStr',
                  style: const TextStyle(
                      color: kEmerald, fontSize: 10, fontWeight: FontWeight.w700)),
              const SizedBox(width: 8),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [
                    kPrimary.withOpacity(0.15),
                    kPrimary.withOpacity(0.04)
                  ]),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(
                      color: kPrimary.withOpacity(0.2), width: 0.5),
                ),
                child: Text(med.frequencyLabel,
                    style: const TextStyle(
                        color: kAccent2,
                        fontSize: 9,
                        fontWeight: FontWeight.w700)),
              ),
            ]),
          ])),
        ]),
      ),
    );
  }

  // ── OCR overlay ───────────────────────────────────────────────────
  Widget _buildScanOverlay() {
    return Positioned.fill(
      child: Container(
        color: Colors.black.withOpacity(0.82),
        child: Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
          Container(
            width: 90, height: 90,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [kPrimary.withOpacity(0.2), kBgCard],
                begin: Alignment.topLeft, end: Alignment.bottomRight,
              ),
              border:
                  Border.all(color: Colors.white.withOpacity(0.12), width: 0.8),
              boxShadow: [
                BoxShadow(color: kPrimary.withOpacity(0.4), blurRadius: 30),
                BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 14),
              ],
            ),
            child: Center(child: SizedBox(
              width: 38, height: 38,
              child: CircularProgressIndicator(
                color: kAccent, strokeWidth: 2.5,
                backgroundColor: kAccent.withOpacity(0.1),
              ),
            )),
          ),
          const SizedBox(height: 22),
          ShaderMask(
            shaderCallback: (b) => gradPrimary.createShader(b),
            blendMode: BlendMode.srcIn,
            child: const Text('Analyse OCR en cours…',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
          ),
          const SizedBox(height: 6),
          const Text('ML Kit lit la boîte du médicament',
              style: TextStyle(color: kMuted, fontSize: 12)),
        ])),
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

// ═══════════════════════════════════════════════════════════════════════
// Formulaire d'ajout de médicament
// ═══════════════════════════════════════════════════════════════════════
class _MedFormSheet extends StatefulWidget {
  final String? prefillName, prefillDosage, prefillFreqLabel;
  final int?    prefillIntervalHours;
  final bool    ocrFound, isUnknownMed;
  final Future<void> Function(Medication) onSave;

  const _MedFormSheet({
    this.prefillName, this.prefillDosage, this.prefillFreqLabel,
    this.prefillIntervalHours, this.ocrFound = false, this.isUnknownMed = false,
    required this.onSave,
  });

  @override
  State<_MedFormSheet> createState() => _MedFormSheetState();
}

class _MedFormSheetState extends State<_MedFormSheet> {
  late final TextEditingController _nameCtrl, _dosageCtrl, _notesCtrl;
  DateTime _nextDose     = DateTime.now().add(const Duration(hours: 8));
  int      _intervalHours = 24;
  String   _freqLabel     = '1x par jour';
  String?  _suggestion;
  bool     _saving        = false;

  static const _freqs = [
    ('Toutes les 8h', 8), ('2x par jour', 12), ('1x par jour', 24),
    ('Hebdomadaire', 168), ('Mensuel', 720), ('Tous les 3 mois', 2160),
    ('Dose unique', 0),
  ];

  @override
  void initState() {
    super.initState();
    _nameCtrl   = TextEditingController(text: widget.prefillName   ?? '');
    _dosageCtrl = TextEditingController(text: widget.prefillDosage ?? '');
    _notesCtrl  = TextEditingController();
    if (widget.prefillFreqLabel    != null) _freqLabel     = widget.prefillFreqLabel!;
    if (widget.prefillIntervalHours != null) _intervalHours = widget.prefillIntervalHours!;
    _nameCtrl.addListener(_onNameChanged);
  }

  void _onNameChanged() {
    final q = _nameCtrl.text.toUpperCase().trim();
    if (q.length < 3) {
      if (_suggestion != null) setState(() => _suggestion = null);
      return;
    }
    final match = MedicationService.allNames
        .firstWhere((n) => n.startsWith(q) && n != q, orElse: () => '');
    final next = match.isEmpty ? null : match;
    if (next != _suggestion) setState(() => _suggestion = next);
  }

  void _applySuggestion(String name) {
    final info = MedicationService.getByName(name);
    setState(() {
      _nameCtrl.text = name;
      _nameCtrl.selection =
          TextSelection.fromPosition(TextPosition(offset: name.length));
      if (info != null) {
        _dosageCtrl.text = info['dosage'] as String;
        _freqLabel       = info['frequencyLabel'] as String;
        _intervalHours   = info['intervalHours'] as int;
      }
      _suggestion = null;
    });
  }

  @override
  void dispose() {
    _nameCtrl.dispose(); _dosageCtrl.dispose(); _notesCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _nextDose,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate : DateTime.now().add(const Duration(days: 365)),
      builder  : (_, child) => Theme(
        data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(primary: kPrimary)),
        child: child!,
      ),
    );
    if (date == null || !mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_nextDose),
      builder : (_, child) => Theme(
        data: ThemeData.dark().copyWith(
            colorScheme: const ColorScheme.dark(primary: kPrimary)),
        child: child!,
      ),
    );
    if (time == null) return;
    setState(() =>
        _nextDose = DateTime(date.year, date.month, date.day, time.hour, time.minute));
  }

  Future<void> _save() async {
    if (_nameCtrl.text.trim().isEmpty) return;
    setState(() => _saving = true);
    final med = Medication(
      id            : DateTime.now().millisecondsSinceEpoch.toString(),
      name          : _nameCtrl.text.trim().toUpperCase(),
      dosage        : _dosageCtrl.text.trim().isEmpty
          ? 'Selon prescription'
          : _dosageCtrl.text.trim(),
      frequencyLabel: _freqLabel,
      intervalHours : _intervalHours,
      nextDose      : _nextDose,
      notes         : _notesCtrl.text.trim().isEmpty ? null : _notesCtrl.text.trim(),
      notificationId: MedicationService.generateNotifId(),
    );
    await widget.onSave(med);
    if (mounted) Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
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
            border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.7),
          ),
          child: Padding(
            padding:
                EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
            child: SingleChildScrollView(
              padding: const EdgeInsets.fromLTRB(22, 14, 22, 32),
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                Center(child: Container(
                  width: 44, height: 4,
                  decoration: BoxDecoration(
                      gradient: gradPrimary,
                      borderRadius: BorderRadius.circular(2)),
                )),
                const SizedBox(height: 18),
                Row(children: [
                  const Text('💊', style: TextStyle(fontSize: 22)),
                  const SizedBox(width: 10),
                  ShaderMask(
                    shaderCallback: (b) => gradPrimary.createShader(b),
                    blendMode: BlendMode.srcIn,
                    child: const Text('Nouveau traitement',
                        style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
                  ),
                  const Spacer(),
                  if (widget.ocrFound)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [
                          kEmerald.withOpacity(0.18),
                          kEmerald.withOpacity(0.06)
                        ]),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                            color: kEmerald.withOpacity(0.3), width: 0.6),
                      ),
                      child: const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.auto_fix_high_rounded,
                            color: kEmerald, size: 11),
                        SizedBox(width: 4),
                        Text('Reconnu',
                            style: TextStyle(
                                color: kEmerald,
                                fontSize: 10,
                                fontWeight: FontWeight.w800)),
                      ]),
                    ),
                  if (widget.isUnknownMed)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [
                          kAmber.withOpacity(0.18),
                          kAmber.withOpacity(0.06)
                        ]),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(
                            color: kAmber.withOpacity(0.3), width: 0.6),
                      ),
                      child: const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.help_outline_rounded,
                            color: kAmber, size: 11),
                        SizedBox(width: 4),
                        Text('Inconnu',
                            style: TextStyle(
                                color: kAmber,
                                fontSize: 10,
                                fontWeight: FontWeight.w800)),
                      ]),
                    ),
                ]),
                if (widget.isUnknownMed) ...[
                  const SizedBox(height: 14),
                  Container(
                    padding: const EdgeInsets.all(13),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(colors: [
                        kAmber.withOpacity(0.1),
                        kAmber.withOpacity(0.03)
                      ]),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                          color: Colors.white.withOpacity(0.08), width: 0.7),
                    ),
                    child: const Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                      Text('🔍', style: TextStyle(fontSize: 16)),
                      SizedBox(width: 10),
                      Expanded(child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                        Text('Médicament non reconnu dans la base',
                            style: TextStyle(
                                color: kAmber,
                                fontSize: 12,
                                fontWeight: FontWeight.w800)),
                        SizedBox(height: 3),
                        Text(
                            'Vérifiez le nom et complétez la posologie. Consultez votre vétérinaire.',
                            style: TextStyle(
                                color: kBody, fontSize: 11, height: 1.4)),
                      ])),
                    ]),
                  ),
                ],
                const SizedBox(height: 22),
                _label('Nom du médicament *'),
                _field(
                    ctrl: _nameCtrl,
                    hint: 'Ex : FRONTLINE, MILBEMAX…',
                    caps: TextCapitalization.characters),
                if (_suggestion != null)
                  GestureDetector(
                    onTap: () => _applySuggestion(_suggestion!),
                    child: Container(
                      margin: const EdgeInsets.only(top: 7),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 13, vertical: 10),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(colors: [
                          kPrimary.withOpacity(0.12),
                          kPrimary.withOpacity(0.04)
                        ]),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                            color: Colors.white.withOpacity(0.08), width: 0.7),
                        boxShadow: [
                          BoxShadow(
                              color: kPrimary.withOpacity(0.15), blurRadius: 8)
                        ],
                      ),
                      child: Row(children: [
                        const Icon(Icons.auto_fix_high_rounded,
                            color: kAccent2, size: 13),
                        const SizedBox(width: 8),
                        Expanded(child: Text('Suggestion : $_suggestion',
                            style: const TextStyle(
                                color: kAccent2,
                                fontSize: 12,
                                fontWeight: FontWeight.w700))),
                        const Icon(Icons.touch_app_rounded,
                            color: kAccent2, size: 13),
                      ]),
                    ),
                  ),
                const SizedBox(height: 16),
                _label('Posologie'),
                _field(ctrl: _dosageCtrl, hint: 'Ex : 1 comprimé / 10 kg'),
                const SizedBox(height: 16),
                _label('Fréquence'),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8, runSpacing: 8,
                  children: _freqs.map((f) {
                    final sel = f.$1 == _freqLabel;
                    return GestureDetector(
                      onTap: () => setState(
                          () { _freqLabel = f.$1; _intervalHours = f.$2; }),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 160),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 13, vertical: 9),
                        decoration: BoxDecoration(
                          gradient: sel
                              ? LinearGradient(colors: [
                                  kPrimary.withOpacity(0.3),
                                  kPrimary.withOpacity(0.12)
                                ])
                              : const LinearGradient(
                                  colors: [kBgCardL, kBgCard]),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                              color: Colors.white
                                  .withOpacity(sel ? 0.12 : 0.06),
                              width: sel ? 1.0 : 0.7),
                          boxShadow: sel
                              ? [
                                  BoxShadow(
                                      color: kPrimary.withOpacity(0.25),
                                      blurRadius: 10,
                                      offset: const Offset(0, 3))
                                ]
                              : [
                                  BoxShadow(
                                      color: Colors.black.withOpacity(0.15),
                                      blurRadius: 4)
                                ],
                        ),
                        child: Text(f.$1, style: TextStyle(
                          color: sel ? Colors.white : kMuted,
                          fontSize: 12,
                          fontWeight: sel ? FontWeight.w800 : FontWeight.w500,
                        )),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 16),
                _label('Première prise'),
                const SizedBox(height: 8),
                GestureDetector(
                  onTap: _pickDateTime,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 14, vertical: 14),
                    decoration: BoxDecoration(
                      gradient:
                          const LinearGradient(colors: [kBgCardL, kBgCard]),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                          color: Colors.white.withOpacity(0.08), width: 0.7),
                      boxShadow: [
                        BoxShadow(color: Colors.black.withOpacity(0.2),
                            blurRadius: 6, offset: const Offset(1, 2))
                      ],
                    ),
                    child: Row(children: [
                      ShaderMask(
                        shaderCallback: (b) => gradPrimary.createShader(b),
                        blendMode: BlendMode.srcIn,
                        child:
                            const Icon(Icons.event_rounded, size: 18),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        '${_nextDose.day.toString().padLeft(2, '0')}/${_nextDose.month.toString().padLeft(2, '0')}/${_nextDose.year}'
                        '  ${_nextDose.hour.toString().padLeft(2, '0')}:${_nextDose.minute.toString().padLeft(2, '0')}',
                        style: const TextStyle(
                            color: kText,
                            fontSize: 13,
                            fontWeight: FontWeight.w700),
                      ),
                      const Spacer(),
                      const Icon(Icons.edit_calendar_rounded,
                          color: kMuted, size: 15),
                    ]),
                  ),
                ),
                const SizedBox(height: 16),
                _label('Notes (optionnel)'),
                _field(
                    ctrl: _notesCtrl,
                    hint: 'Observations, ordonnance…',
                    maxLines: 2),
                const SizedBox(height: 28),
                GestureDetector(
                  onTap: (_saving || _nameCtrl.text.trim().isEmpty)
                      ? null
                      : _save,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(vertical: 15),
                    decoration: BoxDecoration(
                      gradient: (_saving || _nameCtrl.text.trim().isEmpty)
                          ? const LinearGradient(colors: [kBgCardL, kBgCard])
                          : const LinearGradient(
                              colors: [Color(0xFF9D5CF6), Color(0xFF7C3AED)],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                          color: Colors.white.withOpacity(
                              (_saving || _nameCtrl.text.trim().isEmpty)
                                  ? 0.06
                                  : 0.15),
                          width: (_saving || _nameCtrl.text.trim().isEmpty)
                              ? 0.7
                              : 0.8),
                      boxShadow: (_saving || _nameCtrl.text.trim().isEmpty)
                          ? [
                              BoxShadow(
                                  color: Colors.black.withOpacity(0.15),
                                  blurRadius: 4)
                            ]
                          : [
                              BoxShadow(
                                  color: const Color(0xFF7C3AED).withOpacity(0.45),
                                  blurRadius: 20,
                                  offset: const Offset(0, 5)),
                              BoxShadow(
                                  color: Colors.black.withOpacity(0.4),
                                  blurRadius: 12,
                                  offset: const Offset(2, 6)),
                            ],
                    ),
                    child: Center(
                      child: _saving
                          ? const SizedBox(
                              width: 22, height: 22,
                              child: CircularProgressIndicator(
                                  color: Colors.white, strokeWidth: 2.5))
                          : Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.notifications_active_rounded,
                                    color: _nameCtrl.text.trim().isEmpty
                                        ? kMuted
                                        : Colors.white,
                                    size: 18),
                                const SizedBox(width: 8),
                                Text('Enregistrer & programmer rappel',
                                    style: TextStyle(
                                      color: _nameCtrl.text.trim().isEmpty
                                          ? kMuted
                                          : Colors.white,
                                      fontWeight: FontWeight.w900,
                                      fontSize: 14,
                                    )),
                              ]),
                    ),
                  ),
                ),
              ]),
            ),
          ),
        ),
      ),
    );
  }

  Widget _label(String text) => Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Text(text,
            style: const TextStyle(
                color: kMuted,
                fontSize: 11.5,
                fontWeight: FontWeight.w600,
                letterSpacing: 0.3)),
      );

  Widget _field({
    required TextEditingController ctrl,
    required String hint,
    int maxLines = 1,
    TextCapitalization caps = TextCapitalization.none,
  }) {
    return TextField(
      controller         : ctrl,
      maxLines           : maxLines,
      textCapitalization : caps,
      style              : const TextStyle(color: kText, fontSize: 13),
      decoration: InputDecoration(
        hintText  : hint,
        hintStyle : const TextStyle(color: kMuted, fontSize: 13),
        filled    : true,
        fillColor : kBgCard,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: kBorder, width: 0.6)),
        enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: kBorder, width: 0.6)),
        focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: kAccent, width: 1.2)),
      ),
    );
  }
}
