import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:geolocator/geolocator.dart';
import 'package:latlong2/latlong.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/api_service.dart';

// ── Cheebo Brand Colors ──────────────────────────────────────────────
const _kBgDark      = Color(0xFF0D0820);
const _kBgCard      = Color(0xFF1A1232);
const _kBgCardLight = Color(0xFF231A40);
const _kPrimary     = Color(0xFF7B56E2);
const _kAccent      = Color(0xFFC084FC);
const _kTextBody    = Color(0xFFD0C0E8);
const _kTextMuted   = Color(0xFF8B7AB0);
const _kSurface     = Color(0xFF2A1F4A);

// Coordonnées par défaut — centre de Tunis
const _kDefaultCenter = LatLng(36.8520, 10.2070);

class VetsMapScreen extends StatefulWidget {
  /// Vets déjà chargés depuis le chat (passage direct) — si null, chargés depuis l'API.
  final List<Map<String, dynamic>>? initialVets;

  const VetsMapScreen({super.key, this.initialVets});

  @override
  State<VetsMapScreen> createState() => _VetsMapScreenState();
}

class _VetsMapScreenState extends State<VetsMapScreen> {
  final MapController _mapController = MapController();

  List<Map<String, dynamic>> _vets    = [];
  Map<String, dynamic>?      _selected;
  LatLng?                    _userPos;
  bool                       _loading = true;
  String?                    _error;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    await Future.wait([_loadVets(), _fetchUserLocation()]);
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _loadVets() async {
    if (widget.initialVets != null && widget.initialVets!.isNotEmpty) {
      _vets = widget.initialVets!;
      return;
    }
    try {
      _vets = await ApiService.getPartnerVets(availableOnly: false);
    } catch (_) {
      _error = 'Impossible de charger les vétérinaires.';
    }
  }

  Future<void> _fetchUserLocation() async {
    try {
      LocationPermission perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm == LocationPermission.denied ||
          perm == LocationPermission.deniedForever) return;

      final pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.medium,
      ).timeout(const Duration(seconds: 8));
      _userPos = LatLng(pos.latitude, pos.longitude);
    } catch (_) {
      // GPS indisponible — carte centrée sur Tunis
    }
  }

  // ── Distance en km entre deux points ──────────────────────────────
  double? _distanceTo(Map<String, dynamic> vet) {
    final lat = (vet['lat'] as num?)?.toDouble();
    final lng = (vet['lng'] as num?)?.toDouble();
    if (lat == null || lng == null || _userPos == null) return null;

    const r = 6371.0;
    final dLat = _toRad(lat - _userPos!.latitude);
    final dLng = _toRad(lng - _userPos!.longitude);
    final a = math.sin(dLat / 2) * math.sin(dLat / 2) +
        math.cos(_toRad(_userPos!.latitude)) *
            math.cos(_toRad(lat)) *
            math.sin(dLng / 2) *
            math.sin(dLng / 2);
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a));
  }

  double _toRad(double deg) => deg * math.pi / 180;

  String _distanceLabel(Map<String, dynamic> vet) {
    final d = _distanceTo(vet);
    if (d == null) return '';
    if (d < 1) return '${(d * 1000).round()} m';
    return '${d.toStringAsFixed(1)} km';
  }

  // ── Zoom vers le marker sélectionné ───────────────────────────────
  void _selectVet(Map<String, dynamic> vet) {
    final lat = (vet['lat'] as num?)?.toDouble();
    final lng = (vet['lng'] as num?)?.toDouble();
    setState(() => _selected = vet);
    if (lat != null && lng != null) {
      _mapController.move(LatLng(lat, lng), 15.5);
    }
  }

  Future<void> _callVet(String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }

  LatLng get _initialCenter {
    if (_userPos != null) return _userPos!;
    final vetsWithCoords = _vets
        .where((v) => v['lat'] != null && v['lng'] != null)
        .toList();
    if (vetsWithCoords.isNotEmpty) {
      return LatLng(
        (vetsWithCoords.first['lat'] as num).toDouble(),
        (vetsWithCoords.first['lng'] as num).toDouble(),
      );
    }
    return _kDefaultCenter;
  }

  // ── Build ─────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _kBgDark,
      body: Stack(
        children: [
          if (_loading)
            const Center(child: CircularProgressIndicator(color: _kAccent))
          else if (_error != null)
            _buildError()
          else
            _buildMap(),

          // App bar flottante
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
              child: Row(
                children: [
                  _floatButton(
                    Icons.arrow_back_ios_rounded,
                    () => Navigator.pop(context),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      decoration: BoxDecoration(
                        color: _kBgCard.withOpacity(0.92),
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: _kPrimary.withOpacity(0.2)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.local_hospital_rounded, color: _kAccent, size: 16),
                          const SizedBox(width: 8),
                          Text(
                            'Vétérinaires partenaires (${_vets.length})',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  // Recentrer sur position utilisateur
                  if (_userPos != null)
                    _floatButton(
                      Icons.my_location_rounded,
                      () => _mapController.move(_userPos!, 14),
                    ),
                ],
              ),
            ),
          ),

          // Panneau vet sélectionné
          if (_selected != null)
            Positioned(
              left: 0,
              right: 0,
              bottom: 0,
              child: _buildVetPanel(_selected!),
            ),

          // Légende en haut à droite
          if (!_loading && _error == null)
            Positioned(
              top: 80,
              right: 12,
              child: _buildLegend(),
            ),
        ],
      ),
    );
  }

  Widget _buildMap() {
    final markers = <Marker>[];

    // Marker position utilisateur
    if (_userPos != null) {
      markers.add(Marker(
        point: _userPos!,
        width: 28,
        height: 28,
        child: Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: Colors.blue.shade600,
            border: Border.all(color: Colors.white, width: 2),
            boxShadow: [BoxShadow(color: Colors.blue.withOpacity(0.4), blurRadius: 8)],
          ),
          child: const Icon(Icons.person_pin_circle_rounded, color: Colors.white, size: 16),
        ),
      ));
    }

    // Markers vétérinaires
    for (final vet in _vets) {
      final lat = (vet['lat'] as num?)?.toDouble();
      final lng = (vet['lng'] as num?)?.toDouble();
      if (lat == null || lng == null) continue;

      final isSelected  = _selected != null && _selected!['id'] == vet['id'];
      final isEmergency = vet['emergency'] == true;

      markers.add(Marker(
        point: LatLng(lat, lng),
        width: isSelected ? 52 : 42,
        height: isSelected ? 52 : 42,
        child: GestureDetector(
          onTap: () => _selectVet(vet),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: isEmergency
                    ? [const Color(0xFFEF4444), const Color(0xFFDC2626)]
                    : [_kAccent, _kPrimary],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              border: Border.all(
                color: isSelected ? Colors.white : Colors.white.withOpacity(0.5),
                width: isSelected ? 3 : 1.5,
              ),
              boxShadow: [
                BoxShadow(
                  color: (isEmergency ? Colors.red : _kPrimary).withOpacity(0.5),
                  blurRadius: isSelected ? 16 : 8,
                  spreadRadius: isSelected ? 2 : 0,
                ),
              ],
            ),
            child: Icon(
              isEmergency ? Icons.emergency_rounded : Icons.pets_rounded,
              color: Colors.white,
              size: isSelected ? 24 : 18,
            ),
          ),
        ),
      ));
    }

    return FlutterMap(
      mapController: _mapController,
      options: MapOptions(
        initialCenter: _initialCenter,
        initialZoom: 13.0,
        onTap: (_, __) => setState(() => _selected = null),
      ),
      children: [
        TileLayer(
          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          userAgentPackageName: 'com.cheebo.healthcare',
          maxZoom: 19,
        ),
        MarkerLayer(markers: markers),
      ],
    );
  }

  Widget _buildVetPanel(Map<String, dynamic> vet) {
    final isEmergency = vet['emergency'] == true;
    final phone       = vet['phone'] as String? ?? '';
    final address     = vet['address'] as String? ?? '';
    final specs       = (vet['specialties'] as List?)?.cast<String>() ?? [];
    final distLabel   = _distanceLabel(vet);

    return Container(
      margin: const EdgeInsets.fromLTRB(12, 0, 12, 16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: _kBgCard,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: isEmergency
              ? Colors.red.withOpacity(0.4)
              : _kPrimary.withOpacity(0.3),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.5),
            blurRadius: 20,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // En-tête
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: LinearGradient(
                    colors: isEmergency
                        ? [const Color(0xFFEF4444), const Color(0xFFDC2626)]
                        : [_kAccent, _kPrimary],
                  ),
                ),
                child: Icon(
                  isEmergency ? Icons.emergency_rounded : Icons.local_hospital_rounded,
                  color: Colors.white,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      vet['name'] ?? '',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    if (distLabel.isNotEmpty)
                      Text(
                        distLabel,
                        style: const TextStyle(color: _kAccent, fontSize: 12),
                      ),
                  ],
                ),
              ),
              if (isEmergency)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: Colors.red.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Colors.red.withOpacity(0.4)),
                  ),
                  child: const Text('URGENCES',
                      style: TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.w700)),
                ),
              const SizedBox(width: 8),
              GestureDetector(
                onTap: () => setState(() => _selected = null),
                child: const Icon(Icons.close_rounded, color: _kTextMuted, size: 20),
              ),
            ],
          ),

          const SizedBox(height: 12),

          // Adresse
          if (address.isNotEmpty) ...[
            Row(
              children: [
                const Icon(Icons.location_on_rounded, color: _kTextMuted, size: 14),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(address,
                      style: const TextStyle(color: _kTextBody, fontSize: 12)),
                ),
              ],
            ),
            const SizedBox(height: 8),
          ],

          // Spécialités
          if (specs.isNotEmpty) ...[
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: specs.map((s) => Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _kSurface,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(s,
                    style: const TextStyle(color: _kTextMuted, fontSize: 11)),
              )).toList(),
            ),
            const SizedBox(height: 12),
          ],

          // Bouton Appeler
          if (phone.isNotEmpty)
            SizedBox(
              width: double.infinity,
              child: GestureDetector(
                onTap: () => _callVet(phone),
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [_kAccent, _kPrimary]),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.phone_rounded, color: Colors.white, size: 16),
                      const SizedBox(width: 8),
                      Text(
                        'Appeler  $phone',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildLegend() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: _kBgCard.withOpacity(0.9),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: _kPrimary.withOpacity(0.2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          _legendItem(Icons.emergency_rounded, Colors.red.shade400, 'Urgences 24/7'),
          const SizedBox(height: 6),
          _legendItem(Icons.pets_rounded, _kAccent, 'Clinique partenaire'),
          if (_userPos != null) ...[
            const SizedBox(height: 6),
            _legendItem(Icons.person_pin_circle_rounded, Colors.blue.shade400, 'Ma position'),
          ],
        ],
      ),
    );
  }

  Widget _legendItem(IconData icon, Color color, String label) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, color: color, size: 14),
        const SizedBox(width: 6),
        Text(label, style: const TextStyle(color: _kTextBody, fontSize: 11)),
      ],
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.wifi_off_rounded, color: _kTextMuted, size: 48),
          const SizedBox(height: 12),
          Text(_error!, style: const TextStyle(color: _kTextMuted, fontSize: 14)),
        ],
      ),
    );
  }

  Widget _floatButton(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: _kBgCard.withOpacity(0.92),
          shape: BoxShape.circle,
          border: Border.all(color: _kPrimary.withOpacity(0.3)),
        ),
        child: Icon(icon, color: _kAccent, size: 18),
      ),
    );
  }
}
