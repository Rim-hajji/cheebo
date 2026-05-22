import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tzData;
import 'api_service.dart';

class NotificationService {
  static final _plugin = FlutterLocalNotificationsPlugin();
  static bool _initialized = false;

  static const _channelId    = 'cheebo_wellness';
  static const _channelName  = 'Bien-être animal';
  static const _notifId      = 1;
  static const _prefArticles = 'cached_articles';

  // Heure de la notification quotidienne (10h00 par défaut)
  static const _notifHour   = 10;
  static const _notifMinute = 0;

  static Future<void> init() async {
    if (_initialized) return;
    tzData.initializeTimeZones();

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const settings = InitializationSettings(android: android);

    await _plugin.initialize(settings);

    // Demande permission Android 13+
    await _plugin
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.requestNotificationsPermission();

    _initialized = true;
  }

  /// Planifie la notification quotidienne automatique.
  /// Appelée au démarrage de l'app — se reprogramme chaque jour à [_notifHour]h.
  static Future<void> scheduleDaily() async {
    await init();

    // Récupère l'article du jour (depuis le cache local si API indisponible)
    final article = await _fetchArticle();

    final title = '${article['icon'] ?? '🐾'} Conseil bien-être — ${article['category'] ?? 'Cheebo'}';
    final body  = article['tip'] ?? article['summary'] ?? 'Découvrez nos conseils pour votre animal.';

    // Calcule la prochaine occurrence de l'heure choisie
    final now       = tz.TZDateTime.now(tz.local);
    var   scheduled = tz.TZDateTime(
      tz.local,
      now.year, now.month, now.day,
      _notifHour, _notifMinute,
    );
    if (scheduled.isBefore(now)) {
      scheduled = scheduled.add(const Duration(days: 1));
    }

    await _plugin.cancel(_notifId);
    await _plugin.zonedSchedule(
      _notifId,
      title,
      body.length > 120 ? '${body.substring(0, 117)}…' : body,
      scheduled,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _channelId,
          _channelName,
          channelDescription: 'Conseils quotidiens bien-être pour votre animal',
          importance        : Importance.high,
          priority          : Priority.high,
          color             : const Color(0xFF7B56E2),
          icon              : '@mipmap/ic_launcher',
          styleInformation  : BigTextStyleInformation(
            body,
            summaryText: article['source'] ?? 'Cheebo Healthcare',
          ),
        ),
      ),
      androidScheduleMode                    : AndroidScheduleMode.exactAllowWhileIdle,
      matchDateTimeComponents                : DateTimeComponents.time,
      uiLocalNotificationDateInterpretation  : UILocalNotificationDateInterpretation.absoluteTime,
      payload                                : jsonEncode(article),
    );

    debugPrint('[Notif] Planifiée pour ${scheduled.hour}h${scheduled.minute.toString().padLeft(2,'0')} — ${article['title']}');
  }

  /// Envoie immédiatement une notification test (pour démo / bouton dans l'écran).
  static Future<void> showNow() async {
    await init();
    final article = await _fetchArticle();
    final title   = '${article['icon'] ?? '🐾'} ${article['category'] ?? 'Bien-être'}';
    final body    = article['tip'] ?? article['summary'] ?? 'Conseil bien-être Cheebo.';

    await _plugin.show(
      99,
      title,
      body.length > 120 ? '${body.substring(0, 117)}…' : body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _channelId,
          _channelName,
          importance      : Importance.high,
          priority        : Priority.high,
          color           : const Color(0xFF7B56E2),
          icon            : '@mipmap/ic_launcher',
          styleInformation: BigTextStyleInformation(
            body,
            summaryText: article['source'] ?? 'Cheebo Healthcare',
          ),
        ),
      ),
      payload: jsonEncode(article),
    );
  }

  // ── Helpers ────────────────────────────────────────────────────────

  /// Récupère l'article du jour — depuis l'API ou le cache local.
  static Future<Map<String, dynamic>> _fetchArticle() async {
    // 1. Essaye l'API
    try {
      final article = await ApiService.getDailyArticle();
      if (article.isNotEmpty) {
        _cacheArticles([article]); // met à jour le cache
        return article;
      }
    } catch (_) {}

    // 2. Fallback : cache local
    final prefs    = await SharedPreferences.getInstance();
    final cached   = prefs.getStringList(_prefArticles) ?? [];
    if (cached.isNotEmpty) {
      final idx = DateTime.now().day % cached.length;
      try { return jsonDecode(cached[idx]) as Map<String, dynamic>; } catch (_) {}
    }

    return {'icon': '🐾', 'category': 'Bien-être', 'tip': 'Pensez à consulter régulièrement votre vétérinaire.', 'source': 'Cheebo'};
  }

  static Future<void> _cacheArticles(List<Map<String, dynamic>> articles) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setStringList(_prefArticles, articles.map(jsonEncode).toList());
    } catch (_) {}
  }

  /// Pré-charge tous les articles en cache local pour usage hors-ligne.
  static Future<void> preloadArticles() async {
    try {
      final articles = await ApiService.getArticles();
      if (articles.isNotEmpty) await _cacheArticles(articles);
    } catch (_) {}
  }
}
