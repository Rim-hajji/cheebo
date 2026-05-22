import 'dart:convert';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tzData;
import '../models/medication.dart';

// ── Base de données médicaments vétérinaires (~50 entrées) ────────────
const _vetDb = <String, Map<String, dynamic>>{
  // ── Antiparasitaires externes ──
  'FRONTLINE'        : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'FRONTLINE COMBO'  : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'FRONTLINE TRI-ACT': {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'ADVOCATE'         : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'STRONGHOLD'       : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'REVOLUTION'       : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'BROADLINE'        : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'NEXGARD'          : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'NEXGARD SPECTRA'  : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'SIMPARICA'        : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'SIMPARICA TRIO'   : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'BRAVECTO'         : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 90 jours',   'intervalHours': 2160},
  'SERESTO'          : {'dosage': '1 collier',                 'frequencyLabel': 'Tous les 8 mois',     'intervalHours': 5760},
  'SCALIBOR'         : {'dosage': '1 collier',                 'frequencyLabel': 'Tous les 6 mois',     'intervalHours': 4320},
  // ── Antiparasitaires internes ──
  'MILBEMAX'         : {'dosage': '1 comprimé / 10 kg',        'frequencyLabel': 'Tous les 3 mois',     'intervalHours': 2160},
  'DRONTAL'          : {'dosage': '1 comprimé / 10 kg',        'frequencyLabel': 'Tous les 3 mois',     'intervalHours': 2160},
  'PROFENDER'        : {'dosage': '1 pipette topique',         'frequencyLabel': 'Tous les 3 mois',     'intervalHours': 2160},
  'PANACUR'          : {'dosage': '1 sachet / jour',           'frequencyLabel': 'Pendant 3 jours',     'intervalHours': 24},
  'INTERCEPTOR'      : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'HEARTGARD'        : {'dosage': '1 comprimé',                'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  // ── Anti-inflammatoires / douleur ──
  'METACAM'          : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'RIMADYL'          : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'PREVICOX'         : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'GALLIPRANT'       : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'ONSIOR'           : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'VETALGIN'         : {'dosage': 'Selon prescription',        'frequencyLabel': 'Au besoin',           'intervalHours': 8},
  // ── Antibiotiques ──
  'SYNULOX'          : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'CLAVAMOX'         : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'AMOXICILLINE'     : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'RILEXINE'         : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'MARBOCYL'         : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'BAYTRIL'          : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'ANTIROBE'         : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'STOMORGYL'        : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'CONVENIA'         : {'dosage': 'Injection unique',          'frequencyLabel': 'Dose unique (14j)',    'intervalHours': 0},
  // ── Dermatologie / allergie ──
  'APOQUEL'          : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour (puis 1x)', 'intervalHours': 12},
  'ATOPICA'          : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'CYTOPOINT'        : {'dosage': 'Injection',                 'frequencyLabel': 'Tous les 30 jours',   'intervalHours': 720},
  'CORTAVANCE'       : {'dosage': '1 application',             'frequencyLabel': '1x par jour',         'intervalHours': 24},
  // ── Corticoïdes ──
  'PREDNISOLONE'     : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'PREDNISONE'       : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  // ── Cardiologie / rein ──
  'VETMEDIN'         : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'CARDALIS'         : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'FORTEKOR'         : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'SEMINTRA'         : {'dosage': 'Selon prescription',        'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'IPAKITINE'        : {'dosage': '1 sachet par repas',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  // ── Thyroïde ──
  'FELIMAZOLE'       : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  // ── Digestif ──
  'FLAGYL'           : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'LACTULOSE'        : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
  'BUSCOPAN'         : {'dosage': 'Selon prescription',        'frequencyLabel': 'Au besoin',           'intervalHours': 0},
  // ── Comportement / anxiété ──
  'ZYLKENE'          : {'dosage': '1 gélule / 10 kg',          'frequencyLabel': '1x par jour',         'intervalHours': 24},
  'ADAPTIL'          : {'dosage': '1 diffuseur',               'frequencyLabel': 'Recharger 30 jours',  'intervalHours': 720},
  'FELIWAY'          : {'dosage': '1 diffuseur',               'frequencyLabel': 'Recharger 30 jours',  'intervalHours': 720},
  'ANXITANE'         : {'dosage': 'Selon prescription',        'frequencyLabel': '2x par jour',         'intervalHours': 12},
};

class MedicationService {
  static const _base    = 'http://127.0.0.1:8000/api/v1';
  static const _petId   = 'default';
  static const _channelId   = 'cheebo_meds';
  static const _channelName = 'Rappels médicaments';

  static final _plugin     = FlutterLocalNotificationsPlugin();
  static bool  _notifReady = false;

  // ── Notifications (device-local) ──────────────────────────────────

  static Future<void> _ensureNotif() async {
    if (_notifReady) return;
    tzData.initializeTimeZones();
    await _plugin.initialize(
      const InitializationSettings(android: AndroidInitializationSettings('@mipmap/ic_launcher')),
    );
    _notifReady = true;
  }

  static Future<void> _schedule(Medication med) async {
    await _ensureNotif();
    final now       = tz.TZDateTime.now(tz.local);
    var   scheduled = tz.TZDateTime.from(med.nextDose, tz.local);
    if (scheduled.isBefore(now)) scheduled = now.add(const Duration(minutes: 5));

    DateTimeComponents? repeat;
    if (med.intervalHours == 24)  repeat = DateTimeComponents.time;
    if (med.intervalHours == 168) repeat = DateTimeComponents.dayOfWeekAndTime;

    await _plugin.zonedSchedule(
      med.notificationId,
      '💊 ${med.name}',
      '${med.dosage} · ${med.frequencyLabel}',
      scheduled,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _channelId, _channelName,
          channelDescription : 'Rappels traitements Cheebo',
          importance         : Importance.high,
          priority           : Priority.high,
          color              : const Color(0xFF7B56E2),
          icon               : '@mipmap/ic_launcher',
        ),
      ),
      androidScheduleMode                   : AndroidScheduleMode.exactAllowWhileIdle,
      uiLocalNotificationDateInterpretation : UILocalNotificationDateInterpretation.absoluteTime,
      matchDateTimeComponents               : repeat,
      payload                               : med.id,
    );
  }

  static Future<void> _cancel(int notifId) async {
    await _ensureNotif();
    await _plugin.cancel(notifId);
  }

  // ── API — lecture ─────────────────────────────────────────────────

  static Future<List<Medication>> loadAll() async {
    try {
      final resp = await http.get(Uri.parse('$_base/medications?pet_id=$_petId'));
      if (resp.statusCode != 200) return [];
      final list = jsonDecode(utf8.decode(resp.bodyBytes)) as List;
      return list
          .map((j) => Medication.fromJson(j as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<List<Medication>> loadHistory() async {
    try {
      final resp = await http.get(Uri.parse('$_base/medications/history?pet_id=$_petId'));
      if (resp.statusCode != 200) return [];
      final list = jsonDecode(utf8.decode(resp.bodyBytes)) as List;
      return list
          .map((j) => Medication.fromJson(j as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  // ── API — écriture ────────────────────────────────────────────────

  static Future<void> add(Medication med) async {
    try {
      await http.post(
        Uri.parse('$_base/medications'),
        headers: {'Content-Type': 'application/json; charset=UTF-8'},
        body: jsonEncode(med.toJson()),
      );
      if (med.isActive && med.intervalHours >= 0) await _schedule(med);
    } catch (_) {}
  }

  static Future<void> delete(Medication med) async {
    try {
      await http.delete(Uri.parse('$_base/medications/${med.id}'));
      await _cancel(med.notificationId);
    } catch (_) {}
  }

  static Future<void> toggleActive(Medication med) async {
    try {
      final resp = await http.put(Uri.parse('$_base/medications/${med.id}/toggle'));
      if (resp.statusCode == 200) {
        final updated = Medication.fromJson(
            jsonDecode(utf8.decode(resp.bodyBytes)) as Map<String, dynamic>);
        if (updated.isActive) {
          await _schedule(updated);
        } else {
          await _cancel(updated.notificationId);
        }
      }
    } catch (_) {}
  }

  static Future<void> complete(Medication med) async {
    try {
      await http.put(Uri.parse('$_base/medications/${med.id}/complete'));
      await _cancel(med.notificationId);
    } catch (_) {}
  }

  // ── Médicaments humains dangereux pour les animaux ────────────────

  static const _humanDangerousMeds = <String, String>{
    'DOLIPRANE'    : 'Le paracétamol est toxique pour chats et chiens — peut causer une insuffisance hépatique.',
    'DAFALGAN'     : 'Le paracétamol est toxique pour chats et chiens — peut causer une insuffisance hépatique.',
    'PARACETAMOL'  : 'Le paracétamol est toxique pour chats et chiens — peut causer une insuffisance hépatique.',
    'TYLENOL'      : 'Le paracétamol est toxique pour chats et chiens — peut causer une insuffisance hépatique.',
    'IBUPROFENE'   : 'L\'ibuprofène peut provoquer ulcères gastriques et insuffisance rénale chez l\'animal.',
    'ADVIL'        : 'L\'ibuprofène peut provoquer ulcères gastriques et insuffisance rénale chez l\'animal.',
    'NUROFEN'      : 'L\'ibuprofène peut provoquer ulcères gastriques et insuffisance rénale chez l\'animal.',
    'ASPIRIN'      : 'L\'aspirine est toxique pour les chats (déficit enzymatique) et dangereuse pour les chiens.',
    'ASPIRINE'     : 'L\'aspirine est toxique pour les chats (déficit enzymatique) et dangereuse pour les chiens.',
    'KARDEGIC'     : 'L\'aspirine est toxique pour les chats et dangereuse pour les chiens.',
    'VOLTAREN'     : 'Le diclofénac est toxique pour les chats — peut causer une insuffisance rénale aiguë.',
    'DICLOFENAC'   : 'Le diclofénac est toxique pour les chats — peut causer une insuffisance rénale aiguë.',
    'AMOXIL'       : 'Antibiotique humain — dosage et formulation différents du vétérinaire, consulter un vétérinaire.',
    'AUGMENTIN'    : 'Antibiotique humain — ne pas administrer sans prescription vétérinaire.',
    'CIPROFLOXACIN': 'Antibiotique humain — peut causer des lésions articulaires chez les jeunes animaux.',
    'ZITHROMAX'    : 'Antibiotique humain — consulter un vétérinaire avant tout usage.',
    'XANAX'        : 'Les benzodiazépines humaines peuvent provoquer sédation excessive ou agitation paradoxale.',
    'VALIUM'       : 'Le diazépam chez le chat peut causer une nécrose hépatique fulminante.',
    'TEMESTA'      : 'Benzodiazépine humaine — ne pas donner sans prescription vétérinaire.',
    'LEXOMIL'      : 'Benzodiazépine humaine — effets imprévisibles chez l\'animal.',
    'PROZAC'       : 'La fluoxétine peut être prescrite par un vétérinaire mais à des doses très différentes.',
    'ZOLOFT'       : 'Antidépresseur humain — ne pas administrer sans prescription vétérinaire.',
    'PLAVIX'       : 'Anticoagulant humain — dosage très différent chez l\'animal, ne pas utiliser sans vétérinaire.',
    'AERIUS'       : 'Antihistaminique humain — consulter un vétérinaire avant usage.',
    'ZYRTEC'       : 'La cétirizine peut être utilisée mais à des doses différentes — consulter un vétérinaire.',
    'SMECTA'       : 'Antidiarrhéique humain — peut masquer une cause grave chez l\'animal.',
    'IMMODIUM'     : 'Le lopéramide est contre-indiqué chez certaines races de chiens (gène MDR1).',
    'IMODIUM'      : 'Le lopéramide est contre-indiqué chez certaines races de chiens (gène MDR1).',
    'PEPTO'        : 'Contient du bismuth salicylate — toxique pour les chats.',
    'GAVISCON'     : 'Non adapté aux animaux — consulter un vétérinaire.',
  };

  // ── OCR parsing ────────────────────────────────────────────────────

  static const _ignoreWords = {
    'MG', 'ML', 'MCG', 'UI', 'CAP', 'CPR', 'TAB', 'SOL', 'INJ', 'LOT',
    'EXP', 'REF', 'VET', 'FOR', 'USE', 'ONLY', 'KEEP', 'OUT', 'READ',
    'DATE', 'BATCH', 'EACH', 'DOSE', 'DOSES', 'BOX', 'SPOT', 'PACK',
  };

  static Map<String, dynamic> parseMedName(String ocrText) {
    final clean = ocrText.toUpperCase().replaceAll(RegExp(r'[^A-Z\s\-]'), ' ');

    final keys = _vetDb.keys.toList()..sort((a, b) => b.length.compareTo(a.length));
    for (final key in keys) {
      if (clean.contains(key)) {
        return {'name': key, ..._vetDb[key]!, 'fromDb': true, 'isDanger': false};
      }
    }

    for (final entry in _humanDangerousMeds.entries) {
      if (clean.contains(entry.key)) {
        return {
          'name'          : entry.key,
          'dosage'        : '',
          'frequencyLabel': '',
          'intervalHours' : 0,
          'fromDb'        : false,
          'isDanger'      : true,
          'dangerMsg'     : entry.value,
        };
      }
    }

    final candidate = _extractCandidateName(clean);
    return {
      'name'          : candidate,
      'dosage'        : '',
      'frequencyLabel': '1x par jour',
      'intervalHours' : 24,
      'fromDb'        : false,
      'isDanger'      : false,
    };
  }

  static String _extractCandidateName(String cleanText) {
    final words = cleanText
        .split(RegExp(r'\s+'))
        .map((w) => w.trim())
        .where((w) => w.length >= 4)
        .where((w) => RegExp(r'^[A-Z]+$').hasMatch(w))
        .where((w) => !_ignoreWords.contains(w))
        .toList();

    if (words.isEmpty) return 'INCONNU';
    words.sort((a, b) => b.length.compareTo(a.length));
    return words.first;
  }

  static List<String> get allNames => _vetDb.keys.toList()..sort();

  static Map<String, dynamic>? getByName(String name) =>
      _vetDb[name.toUpperCase().trim()];

  static int generateNotifId() => Random().nextInt(90000) + 10000;
}
