import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://127.0.0.1:8000/api/v1';
   //static const String  baseUrl = 'http://192.168.1.14:8000/api/v1';

  static Future<Map<String, dynamic>> analyzeSymptoms(String text) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/analyze'),
        headers: {'Content-Type': 'application/json; charset=UTF-8'},
        body: jsonEncode({'text': text}),
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        await _saveToHistory(text, data);
        return data;
      } else {
        throw Exception('Erreur API du Backend: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Impossible de contacter le serveur Python: $e');
    }
  }

  static Future<void> _saveToHistory(String originalText, Map<String, dynamic> data) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String> history = prefs.getStringList('cheebo_history') ?? [];
      final urgency = data['urgency'] ?? {};
      final historyItem = {
        'date': DateTime.now().toIso8601String(),
        'text': originalText,
        'urgency_label': urgency['level'] ?? 'LOW',
        'score': urgency['score'] ?? 0,
      };
      history.insert(0, jsonEncode(historyItem));
      await prefs.setStringList('cheebo_history', history);
    } catch (_) {}
  }

  static Future<List<Map<String, dynamic>>> getHistory() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String> history = prefs.getStringList('cheebo_history') ?? [];
      return history.map((item) => jsonDecode(item) as Map<String, dynamic>).toList();
    } catch (_) {
      return [];
    }
  }

  static Future<Map<String, dynamic>> sendChatMessage({
    required String message,
    String? sessionId,
    List<Map<String, dynamic>> history = const [],
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {'Content-Type': 'application/json; charset=UTF-8'},
        body: jsonEncode({
          'message': message,
          'session_id': sessionId,
          'history': history,
        }),
      );
      if (response.statusCode == 200) {
        return jsonDecode(utf8.decode(response.bodyBytes));
      } else {
        throw Exception('Erreur Chat API: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Serveur inaccessible: $e');
    }
  }

  static Future<Map<String, dynamic>> sendImageMessage({
    required List<XFile> images,
    String message = '',
    String? sessionId,
    List<Map<String, dynamic>> history = const [],
  }) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/chat/image'),
      );
      request.fields['message']      = message;
      request.fields['session_id']   = sessionId ?? '';
      request.fields['history_json'] = jsonEncode(history);
      for (final img in images) {
        final bytes = await img.readAsBytes();
        request.files.add(http.MultipartFile.fromBytes('images', bytes, filename: img.name));
      }
      // Timeout 2.5 min : Groq Vision × N images + pipeline agents
      final streamed = await request.send().timeout(const Duration(seconds: 150));
      final body = await streamed.stream
          .bytesToString()
          .timeout(const Duration(seconds: 150));
      if (streamed.statusCode == 200) {
        return jsonDecode(body) as Map<String, dynamic>;
      }
      throw Exception('Erreur image API: ${streamed.statusCode}');
    } catch (e) {
      throw Exception('Serveur inaccessible: $e');
    }
  }

  static Future<Map<String, dynamic>> sendVideoMessage({
    required XFile video,
    String message = '',
    String? sessionId,
    List<Map<String, dynamic>> history = const [],
  }) async {
    try {
      final request = http.MultipartRequest(
        'POST',
        Uri.parse('$baseUrl/chat/video'),
      );
      request.fields['message']      = message;
      request.fields['session_id']   = sessionId ?? '';
      request.fields['history_json'] = jsonEncode(history);
      final bytes = await video.readAsBytes();
      request.files.add(
        http.MultipartFile.fromBytes('video', bytes, filename: video.name),
      );
      // Timeout 3 min : extraction + 3× Groq Vision + retries 429 éventuels + pipeline
      final streamed = await request.send().timeout(const Duration(seconds: 180));
      final body = await streamed.stream
          .bytesToString()
          .timeout(const Duration(seconds: 180));
      if (streamed.statusCode == 200) {
        return jsonDecode(body) as Map<String, dynamic>;
      }
      throw Exception('Erreur vidéo API: ${streamed.statusCode}');
    } catch (e) {
      throw Exception('Serveur inaccessible: $e');
    }
  }

  // ── Session management ──────────────────────────────────────────

  static Future<void> saveChatSession(Map<String, dynamic> session) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String> sessions = prefs.getStringList('cheebo_sessions') ?? [];
      sessions.removeWhere((s) {
        try { return jsonDecode(s)['session_id'] == session['session_id']; }
        catch (_) { return false; }
      });
      sessions.insert(0, jsonEncode(session));
      if (sessions.length > 30) sessions.removeLast();
      await prefs.setStringList('cheebo_sessions', sessions);
    } catch (_) {}
  }

  static Future<List<Map<String, dynamic>>> getChatSessions() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String> sessions = prefs.getStringList('cheebo_sessions') ?? [];
      return sessions
          .map((s) { try { return jsonDecode(s) as Map<String, dynamic>; } catch (_) { return null; } })
          .whereType<Map<String, dynamic>>()
          .toList();
    } catch (_) {
      return [];
    }
  }

  static Future<void> deleteChatSession(String sessionId) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final List<String> sessions = prefs.getStringList('cheebo_sessions') ?? [];
      sessions.removeWhere((s) {
        try { return jsonDecode(s)['session_id'] == sessionId; }
        catch (_) { return false; }
      });
      await prefs.setStringList('cheebo_sessions', sessions);
    } catch (_) {}
  }

  // ── MongoDB-backed endpoints ────────────────────────────────────

  /// Stats agrégées depuis MongoDB pour le Dashboard.
  static Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/stats'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      }
    } catch (_) {}
    return {};
  }

  /// Liste des conversations depuis MongoDB.
  static Future<List<Map<String, dynamic>>> getConversations({int limit = 50}) async {
    try {
      final response = await http
          .get(Uri.parse('$baseUrl/conversations?limit=$limit'))
          .timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final list = jsonDecode(utf8.decode(response.bodyBytes)) as List;
        return list.cast<Map<String, dynamic>>();
      }
    } catch (_) {}
    return [];
  }

  /// Supprime une conversation depuis MongoDB.
  static Future<bool> deleteConversationRemote(String sessionId) async {
    try {
      final response = await http
          .delete(Uri.parse('$baseUrl/conversations/$sessionId'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 204;
    } catch (_) {
      return false;
    }
  }

  /// Liste des vétérinaires partenaires depuis MongoDB.
  static Future<List<Map<String, dynamic>>> getPartnerVets({
    bool emergencyOnly = false,
    bool availableOnly = true,
  }) async {
    try {
      final uri = Uri.parse(
        '$baseUrl/partner-vets?emergency_only=$emergencyOnly&available_only=$availableOnly',
      );
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final list = jsonDecode(utf8.decode(response.bodyBytes)) as List;
        return list.cast<Map<String, dynamic>>();
      }
    } catch (_) {}
    return [];
  }

  /// Vétérinaires proches triés par distance GPS (Haversine côté serveur).
  static Future<List<Map<String, dynamic>>> getNearbyVets({
    required double lat,
    required double lng,
    double radiusKm = 100,
    int limit = 5,
  }) async {
    try {
      final uri = Uri.parse(
        '$baseUrl/vets/nearby?lat=$lat&lng=$lng&radius_km=$radiusKm&limit=$limit',
      );
      final response = await http.get(uri).timeout(const Duration(seconds: 6));
      if (response.statusCode == 200) {
        final list = jsonDecode(utf8.decode(response.bodyBytes)) as List;
        return list.cast<Map<String, dynamic>>();
      }
    } catch (_) {}
    return [];
  }

  /// Articles d'information vétérinaire depuis MongoDB.
  static Future<List<Map<String, dynamic>>> getArticles() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/articles'),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final list = jsonDecode(utf8.decode(response.bodyBytes)) as List;
        return list.cast<Map<String, dynamic>>();
      }
    } catch (_) {}
    return [];
  }

  /// Article du jour aléatoire.
  static Future<Map<String, dynamic>> getDailyArticle() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/articles?limit=1'),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final list = jsonDecode(utf8.decode(response.bodyBytes)) as List;
        return list.isNotEmpty ? list.first as Map<String, dynamic> : {};
      }
    } catch (_) {}
    return {};
  }

  /// Récupère une conversation spécifique avec tous ses messages.
  static Future<Map<String, dynamic>> getConversationDetail(String sessionId) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/conversations/$sessionId'),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      }
    } catch (e) {
      debugPrint('Erreur getConversationDetail: $e');
    }
    return {};
  }

  /// Historique d'analyse depuis MongoDB (/analysis-history endpoint).
  static Future<List<Map<String, dynamic>>> getAnalysisHistory({int limit = 100}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/analysis-history?limit=$limit'),
      ).timeout(const Duration(seconds: 5));
      if (response.statusCode == 200) {
        final list = jsonDecode(utf8.decode(response.bodyBytes)) as List;
        return list.cast<Map<String, dynamic>>();
      }
    } catch (e) {
      debugPrint('Erreur getAnalysisHistory: $e');
    }
    return [];
  }
}
