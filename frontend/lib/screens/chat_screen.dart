import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:url_launcher/url_launcher.dart';
import 'package:geolocator/geolocator.dart';
import '../services/api_service.dart';
import '../services/ws_service.dart';

// ─── Cheebo Brand Colors ─────────────────────────────────────────────
const kBgDark = Color(0xFF0D0820);
const kBgCard = Color(0xFF1A1232);
const kBgCardLight = Color(0xFF231A40);
const kPrimary = Color(0xFF7B56E2);
const kSecondary = Color(0xFF9A7BF2);
const kAccent = Color(0xFFC084FC);
const kSurface = Color(0xFF2A1F4A);
const kTextMuted = Color(0xFF8B7AB0);
const kTextBody = Color(0xFFD0C0E8);
const kGradientStart = Color(0xFF3D2B8E);
const kGradientEnd = Color(0xFF7B56E2);
const kUserBubbleStart = Color(0xFF8B5CF6);
const kUserBubbleEnd = Color(0xFF6D28D9);

class ChatMessage {
  final String role; // "user" | "agent"
  final String content;
  final String? agentType;
  final DateTime timestamp;
  final List<Map<String, dynamic>>? partnerVets;
  final List<Uint8List>? imagesBytes;
  final bool hasImages;
  final String? videoName; // nom du fichier vidéo joint (affichage uniquement)

  ChatMessage({
    required this.role,
    required this.content,
    this.agentType,
    this.partnerVets,
    this.imagesBytes,
    this.videoName,
    bool? hasImages,
    DateTime? timestamp,
  }) : hasImages = hasImages ?? (imagesBytes?.isNotEmpty ?? false),
       timestamp = timestamp ?? DateTime.now();
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
  // Cache statique : survit à la navigation et aux rebuilds du widget.
  // Clé = "${sessionId}_${timestamp.millisecondsSinceEpoch}"
  static final Map<String, Uint8List> _imgCache = {};

  final GlobalKey<ScaffoldState> _scaffoldKey = GlobalKey<ScaffoldState>();
  final List<ChatMessage> _messages = [];
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();
  String? _sessionId;
  String _sessionTitle = 'Nouvelle conversation';
  List<Map<String, dynamic>> _savedSessions = [];
  bool _isTyping = false;
  bool _isListening = false;
  bool _suppressNextGreeting = false;
  final WsService _wsService = WsService();
  // ignore: cancel_subscriptions
  StreamSubscription<Map<String, dynamic>>? _wsSub;
  bool _hasText = false;
  final List<XFile>    _pendingImages      = [];
  final List<Uint8List> _pendingImagesBytes = [];
  XFile? _pendingVideo;
  late stt.SpeechToText _speech;
  final FlutterTts _tts = FlutterTts();
  String? _speakingId; // timestamp-based ID du message en cours de lecture
  late AnimationController _typingController;
  late AnimationController _pulseController;
  late AnimationController _sendButtonController;

  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();

    _typingController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1200),
    )..repeat();

    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    )..repeat(reverse: true);

    _sendButtonController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 200),
    );

    _textController.addListener(() {
      final hasText = _textController.text.trim().isNotEmpty;
      if (hasText != _hasText) {
        setState(() => _hasText = hasText);
        if (hasText) {
          _sendButtonController.forward();
        } else {
          _sendButtonController.reverse();
        }
      }
    });

    // TTS — handlers de fin et d'erreur
    _tts.setCompletionHandler(() {
      if (mounted) setState(() => _speakingId = null);
    });
    _tts.setErrorHandler((_) {
      if (mounted) setState(() => _speakingId = null);
    });
    _tts.setCancelHandler(() {
      if (mounted) setState(() => _speakingId = null);
    });

    // Ouvrir la connexion WebSocket et charger l'historique
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _connectWebSocket();
      _loadSavedSessions();
    });
  }

  @override
  void dispose() {
    _wsSub?.cancel();
    _wsService.dispose();
    _tts.stop();
    _typingController.dispose();
    _pulseController.dispose();
    _sendButtonController.dispose();
    _textController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  // ── TTS ────────────────────────────────────────────────────────

  /// Supprime le Markdown et les emojis pour une lecture TTS propre.
  String _stripMarkdown(String text) {
    var t = text;
    // Supprimer le préfixe visuel "📸 **Analyse de la photo**\n_..._\n\n"
    t = t.replaceAll(RegExp(r'📸\s*\*\*[^\n]*\*\*\n_[^\n]*_\n\n?'), '');
    // Supprimer les titres Markdown
    t = t.replaceAll(RegExp(r'#{1,6}\s*'), '');
    // Supprimer le gras / italique
    t = t.replaceAll(RegExp(r'\*{1,3}'), '');
    t = t.replaceAll(RegExp(r'_{1,2}([^_]+)_{1,2}'), r'$1');
    t = t.replaceAll('_', '');
    // Remplacer les puces par une ponctuation lisible
    t = t.replaceAll('•', '.');
    // Supprimer les emojis (plages Unicode)
    t = t.replaceAll(
      RegExp(
        r'[\u{1F000}-\u{1FFFF}]|[\u{2600}-\u{27BF}]|[\u{2300}-\u{23FF}]|[\u{FE00}-\u{FE0F}]',
        unicode: true,
      ),
      '',
    );
    // Nettoyer espaces et sauts de ligne superflus
    t = t.replaceAll(RegExp(r' {2,}'), ' ');
    t = t.replaceAll(RegExp(r'\n{3,}'), '\n\n');
    return t.trim();
  }

  /// Détecte la langue du message pour le moteur TTS.
  String _detectTtsLang(String text) {
    if (RegExp(r'[؀-ۿ]').hasMatch(text)) return 'ar-SA';
    if (RegExp(r'\b(the|is|are|your|pet|dog|cat|please|contact|vet)\b')
        .hasMatch(text.toLowerCase())) return 'en-US';
    return 'fr-FR';
  }

  /// Lance la lecture TTS d'un message. Re-appelé sur le même message → stop.
  Future<void> _speak(String text, String messageId) async {
    if (_speakingId == messageId) {
      await _tts.stop();
      if (mounted) setState(() => _speakingId = null);
      return;
    }
    await _tts.stop();

    final lang = _detectTtsLang(text);
    await _tts.setLanguage(lang);
    await _tts.setSpeechRate(lang == 'ar-SA' ? 0.45 : 0.50);
    await _tts.setVolume(1.0);
    await _tts.setPitch(1.0);

    if (mounted) setState(() => _speakingId = messageId);
    await _tts.speak(_stripMarkdown(text));
  }

  /// Bouton "Écouter / Arrêter" affiché sous chaque bulle agent.
  Widget _buildTtsButton(ChatMessage message) {
    final msgId    = message.timestamp.millisecondsSinceEpoch.toString();
    final isSpeaking = _speakingId == msgId;

    return GestureDetector(
      onTap: () => _speak(message.content, msgId),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(
          color: isSpeaking ? kPrimary.withOpacity(0.15) : Colors.transparent,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isSpeaking ? kPrimary.withOpacity(0.35) : Colors.transparent,
            width: 1,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              isSpeaking ? Icons.stop_circle_rounded : Icons.volume_up_rounded,
              size: 13,
              color: isSpeaking ? kAccent : kTextMuted,
            ),
            const SizedBox(width: 4),
            Text(
              isSpeaking ? 'Arrêter' : 'Écouter',
              style: TextStyle(
                fontSize: 11,
                color: isSpeaking ? kAccent : kTextMuted,
                fontWeight: isSpeaking ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── WebSocket ───────────────────────────────────────────────────

  void _connectWebSocket() {
    _wsSub?.cancel();
    _wsService.connect();
    setState(() => _isTyping = true);

    _wsSub = _wsService.stream.listen(
      _handleWsMessage,
      onError: (_) {
        if (!mounted) return;
        setState(() => _isTyping = false);
        _addAgentMessage(
          "😔 Connexion au serveur perdue. Vérifiez que le backend est démarré.",
          "ERROR",
        );
      },
    );
  }

  void _handleWsMessage(Map<String, dynamic> msg) {
    if (!mounted) return;
    final type = msg['type'] as String?;

    switch (type) {
      case 'greeting':
        _sessionId = msg['session_id'] as String?;
        setState(() => _isTyping = false);
        if (!_suppressNextGreeting) {
          _addAgentMessage(msg['response'] as String? ?? '', msg['agent_type'] as String?);
        }
        _suppressNextGreeting = false;
        break;

      case 'status':
        // Indicateur de chargement déjà visible — rien à faire
        break;

      case 'done':
        if (msg.containsKey('session_id')) _sessionId = msg['session_id'] as String?;
        final agentType = msg['agent_type'] as String?;
        if (agentType == 'EMERGENCY') {
          // Urgence → on cherche les vets géographiquement proches avant d'afficher
          _handleEmergencyWithLocation(msg);
        } else {
          final rawVets = msg['partner_vets'] as List<dynamic>?;
          final vets = rawVets?.map((v) => Map<String, dynamic>.from(v as Map)).toList();
          setState(() => _isTyping = false);
          _addAgentMessage(msg['response'] as String? ?? '', agentType, vets: vets);
          _saveCurrentSession();
        }
        break;

      case 'error':
        setState(() => _isTyping = false);
        _addAgentMessage(
          msg['response'] as String? ?? msg['message'] as String? ?? "😔 Erreur technique.",
          "ERROR",
        );
        break;

      case 'disconnected':
      case 'connection_error':
        setState(() => _isTyping = false);
        break;
    }
  }


  void _addAgentMessage(String content, String? type,
      {List<Map<String, dynamic>>? vets}) {
    final msg = ChatMessage(
      role: 'agent',
      content: content,
      agentType: type,
      partnerVets: vets,
    );
    setState(() => _messages.add(msg));
    Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);

    // Lecture automatique pour les urgences CRITICAL/HIGH
    if (type == 'EMERGENCY' && content.length > 20) {
      final msgId = msg.timestamp.millisecondsSinceEpoch.toString();
      Future.delayed(const Duration(milliseconds: 600), () => _speak(content, msgId));
    }
  }

  /// Urgence CRITICAL/HIGH : récupère la position GPS → vets proches → affiche.
  Future<void> _handleEmergencyWithLocation(Map<String, dynamic> msg) async {
    List<Map<String, dynamic>>? nearbyVets;
    try {
      LocationPermission perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) {
        perm = await Geolocator.requestPermission();
      }
      if (perm != LocationPermission.denied && perm != LocationPermission.deniedForever) {
        final pos = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.low,
          timeLimit: const Duration(seconds: 6),
        );
        nearbyVets = await ApiService.getNearbyVets(
          lat: pos.latitude,
          lng: pos.longitude,
        );
      }
    } catch (_) {}

    // Fallback : vets envoyés par le serveur (hardcodés)
    if (nearbyVets == null || nearbyVets.isEmpty) {
      final raw = msg['partner_vets'] as List<dynamic>?;
      nearbyVets = raw?.map((v) => Map<String, dynamic>.from(v as Map)).toList();
    }

    if (!mounted) return;
    setState(() => _isTyping = false);
    _addAgentMessage(
      msg['response'] as String? ?? '',
      msg['agent_type'] as String?,
      vets: nearbyVets,
    );
    _saveCurrentSession();
  }

  // ── Session management ──────────────────────────────────────────

  Future<void> _loadSavedSessions() async {
    try {
      // Charger depuis MongoDB en priorité
      final dbSessions = await ApiService.getConversations(limit: 50);
      
      // Transformer les données de MongoDB en format compatible
      final sessions = dbSessions.map((s) {
        return {
          'session_id': s['session_id'],
          'title': s['title'] ?? 'Conversation',
          'date': s['updated_at'] ?? DateTime.now().toIso8601String(),
          'messages': [],  // Les messages seront chargés à la demande
        };
      }).toList();
      
      if (mounted) setState(() => _savedSessions = sessions);
    } catch (e) {
      debugPrint('Erreur chargement conversations MongoDB: $e');
      // Fallback : charger depuis SharedPreferences
      try {
        final localSessions = await ApiService.getChatSessions();
        if (mounted) setState(() => _savedSessions = localSessions);
      } catch (_) {}
    }
  }

  Future<void> _saveCurrentSession() async {
    if (_sessionId == null) return;
    final userMsgs = _messages.where((m) => m.role == 'user').toList();
    if (userMsgs.isEmpty) return;
    final raw = userMsgs.first.content;
    final title = raw.length > 45 ? '${raw.substring(0, 45)}…' : raw;
    final session = {
      'session_id': _sessionId,
      'title': title,
      'date': DateTime.now().toIso8601String(),
      'messages': _messages
          .map((m) => {
                'role': m.role,
                'content': m.content,
                'agentType': m.agentType,
                'timestamp': m.timestamp.toIso8601String(),
                'partnerVets': m.partnerVets,
                'imagesBase64': m.imagesBytes?.map(base64Encode).toList(),
                'hasImages': m.hasImages,
              })
          .toList(),
    };
    await ApiService.saveChatSession(session);
    await _loadSavedSessions();
  }

  void _newChat() {
    if (Navigator.canPop(context)) Navigator.pop(context);
    setState(() {
      _messages.clear();
      _sessionId = null;
      _sessionTitle = 'Nouvelle conversation';
    });
    _connectWebSocket();
  }

  void _loadSession(Map<String, dynamic> session) {
    if (Navigator.canPop(context)) Navigator.pop(context);
    
    // Essayer de charger les messages complets depuis MongoDB si sessionId est disponible
    final sessionId = session['session_id'] as String?;
    if (sessionId != null) {
      _loadSessionFromDB(sessionId, session);
    } else {
      // Fallback : utiliser les messages fournis (SharedPreferences)
      _loadSessionLocal(session);
    }
  }

  Future<void> _loadSessionFromDB(String sessionId, Map<String, dynamic> fallback) async {
    try {
      // Priorité : cache local (contient imageBase64)
      final localSessions = await ApiService.getChatSessions();
      final local = localSessions.firstWhere(
        (s) => s['session_id']?.toString() == sessionId,
        orElse: () => <String, dynamic>{},
      );
      if (local.isNotEmpty && (local['messages'] as List? ?? []).isNotEmpty) {
        if (mounted) _loadSessionLocal(local);
        return;
      }

      // Fallback MongoDB (texte uniquement, pas d'images)
      final detailedSession = await ApiService.getConversationDetail(sessionId);
      if (detailedSession.isNotEmpty && mounted) {
        _loadSessionLocal(detailedSession);
      } else {
        if (mounted) _loadSessionLocal(fallback);
      }
    } catch (e) {
      debugPrint('Erreur chargement conversation: $e');
      if (mounted) _loadSessionLocal(fallback);
    }
  }

  void _loadSessionLocal(Map<String, dynamic> session) {
    final rawMsgs = session['messages'] as List<dynamic>? ?? [];
    final sid = session['session_id']?.toString();
    final messages = rawMsgs.map((m) {
      final vetsRaw = m['partner_vets'] as List<dynamic>? ?? m['partnerVets'] as List<dynamic>?;
      final vets = vetsRaw?.map((v) => Map<String, dynamic>.from(v as Map)).toList();
      final ts = DateTime.tryParse(m['timestamp']?.toString() ?? '') ?? DateTime.now();

      // 1) Liste de base64 depuis SharedPreferences (imagesBase64)
      List<Uint8List>? imgList;
      try {
        final raw = m['imagesBase64'];
        if (raw is List && raw.isNotEmpty) {
          imgList = raw.map((e) => base64Decode(e.toString())).toList();
        }
      } catch (_) {}

      // 2) Liste depuis MongoDB (images_base64)
      if (imgList == null) {
        try {
          final raw = m['images_base64'];
          if (raw is List && raw.isNotEmpty) {
            imgList = raw.map((e) => base64Decode(e.toString())).toList();
          }
        } catch (_) {}
      }

      // 3) Ancien format single base64 (rétrocompatibilité)
      if (imgList == null) {
        try {
          final b64 = (m['imageBase64'] ?? m['image_base64'])?.toString();
          if (b64 != null && b64.isNotEmpty) imgList = [base64Decode(b64)];
        } catch (_) {}
      }

      // 4) Fallback : cache mémoire (même session navigateur)
      if (imgList == null && sid != null) {
        final cached = <Uint8List>[];
        for (int i = 0; ; i++) {
          final bytes = _imgCache['${sid}_${ts.millisecondsSinceEpoch}_$i'];
          if (bytes == null) break;
          cached.add(bytes);
        }
        if (cached.isNotEmpty) imgList = cached;
      }

      final savedHasImages = m['hasImages'] as bool? ?? m['has_images'] as bool?;
      return ChatMessage(
        role: m['role']?.toString() ?? 'agent',
        content: m['content']?.toString() ?? '',
        agentType: m['agent_type']?.toString() ?? m['agentType']?.toString(),
        partnerVets: vets,
        imagesBytes: imgList,
        hasImages: savedHasImages ?? imgList != null,
        timestamp: ts,
      );
    }).toList();
    setState(() {
      _messages
        ..clear()
        ..addAll(messages);
      _sessionId = session['session_id'] as String?;
      _sessionTitle = session['title'] as String? ?? 'Conversation';
    });
    // Reconnecter le WS pour couper toute réponse en transit de la conversation précédente.
    // Le greeting du nouveau WS est supprimé pour ne pas polluer la vue chargée.
    _suppressNextGreeting = true;
    _connectWebSocket();
    WidgetsBinding.instance.addPostFrameCallback((_) => _scrollToBottom());
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOutCubic,
      );
    }
  }

  Future<void> _sendMessage(String text) async {
    if (_isTyping) return;
    final imgs      = List<XFile>.from(_pendingImages);
    final imgsBytes = List<Uint8List>.from(_pendingImagesBytes);
    final vid       = _pendingVideo;
    if (text.trim().isEmpty && imgsBytes.isEmpty && vid == null) return;
    _textController.clear();
    _focusNode.requestFocus();

    setState(() {
      _messages.add(ChatMessage(
        role: 'user',
        content: text,
        imagesBytes: imgsBytes.isEmpty ? null : imgsBytes,
        videoName: vid?.name,
      ));
      _isTyping = true;
      _pendingImages.clear();
      _pendingImagesBytes.clear();
      _pendingVideo = null;
    });
    Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);

    // ── Texte seul → WebSocket ────────────────────────────────────
    if (imgs.isEmpty && vid == null) {
      _wsService.sendMessage(message: text);
      return; // La réponse arrive via _handleWsMessage
    }

    // ── Image / vidéo → HTTP ─────────────────────────────────────
    try {
      final historyForApi = _messages
          .map((m) => {'role': m.role, 'content': m.content, 'has_images': m.hasImages})
          .toList();

      final Map<String, dynamic> resp;
      if (vid != null) {
        resp = await ApiService.sendVideoMessage(
          video: vid,
          message: text,
          sessionId: _sessionId,
          history: historyForApi,
        );
      } else {
        resp = await ApiService.sendImageMessage(
          images: imgs,
          message: text,
          sessionId: _sessionId,
          history: historyForApi,
        );
      }

      _sessionId = resp['session_id'];
      for (final m in _messages) {
        if (m.imagesBytes != null && _sessionId != null) {
          for (int i = 0; i < m.imagesBytes!.length; i++) {
            _imgCache['${_sessionId}_${m.timestamp.millisecondsSinceEpoch}_$i'] = m.imagesBytes![i];
          }
        }
      }
      final rawVets = resp['partner_vets'] as List<dynamic>?;
      final vets = rawVets?.map((v) => Map<String, dynamic>.from(v as Map)).toList();
      if (mounted) {
        setState(() => _isTyping = false);
        _addAgentMessage(resp['response'] ?? '', resp['agent_type'], vets: vets);
        _saveCurrentSession();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isTyping = false);
        final err = e.toString();
        final isTimeout = err.contains('TimeoutException') || err.contains('timeout');
        final isVideo   = vid != null;
        String errorMsg;
        if (isTimeout && isVideo) {
          errorMsg = "⏳ Délai dépassé — l'analyse vidéo peut prendre jusqu'à 3 minutes. Réessayez dans un instant.";
        } else if (isTimeout) {
          errorMsg = "⏳ L'analyse de la photo prend un peu de temps. Réessayez dans quelques secondes — le serveur a probablement terminé l'analyse.";
        } else if (err.contains('SocketException') || err.contains('Connection refused') || err.contains('inaccessible')) {
          errorMsg = "😔 Impossible de joindre le serveur. Vérifiez que le backend est démarré.";
        } else {
          errorMsg = "😔 Une erreur est survenue. Réessayez dans un instant.";
        }
        _addAgentMessage(errorMsg, "ERROR");
      }
    }
  }

  void _listen() async {
    if (!_isListening) {
      bool available = await _speech.initialize(
        onStatus: (val) {
          if (val == 'done' || val == 'notListening') {
            setState(() => _isListening = false);
          }
        },
        onError: (val) => debugPrint('STT error: $val'),
      );
      if (available) {
        setState(() => _isListening = true);
        _speech.listen(
          onResult: (val) =>
              setState(() => _textController.text = val.recognizedWords),
          localeId: 'fr_FR',
        );
      }
    } else {
      setState(() => _isListening = false);
      _speech.stop();
    }
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

  String _formatTime(DateTime time) {
    return '${time.hour.toString().padLeft(2, '0')}:${time.minute.toString().padLeft(2, '0')}';
  }

  String _getAgentLabel(String? type) {
    switch (type) {
      case 'EMERGENCY':
        return '🚨 Urgence';
      case 'GREETING':
        return '👋 Accueil';
      case 'ANALYSIS':
        return '💡 Conseil préventif';
      case 'QUESTION':
        return '❓ Question de suivi';
      case 'ERROR':
        return '⚠️ Erreur';
      default:
        return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      key: _scaffoldKey,
      backgroundColor: kBgDark,
      drawer: _buildDrawer(),
      body: SafeArea(
        child: Stack(
          children: [
            // Ambient glow background
            _buildAmbientBackground(),
            // Main content
            Column(
              children: [
                _buildAppBar(),
                Expanded(child: _buildMessageList()),
                if (_isTyping) _buildTypingIndicator(),
                _buildInputBar(),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAmbientBackground() {
    return Positioned.fill(
      child: CustomPaint(painter: _AmbientGlowPainter()),
    );
  }

  Widget _buildAppBar() {
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
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 12),
            child: Row(
              children: [
                // Drawer button
                GestureDetector(
                  onTap: () => _scaffoldKey.currentState?.openDrawer(),
                  child: Container(
                    width: 38, height: 38,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle, color: kSurface,
                      border: Border.all(color: kPrimary.withOpacity(0.2)),
                    ),
                    child: const Icon(Icons.menu_rounded, color: kTextMuted, size: 18),
                  ),
                ),
                const SizedBox(width: 8),
                // Avatar with gradient ring
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(
                      colors: [kAccent, kPrimary, kGradientStart],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                  ),
                  child: Container(
                    margin: const EdgeInsets.all(2),
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: kBgCard,
                    ),
                    child: const Center(
                      child: Text('🐾', style: TextStyle(fontSize: 20)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                // Name + subtitle
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      RichText(
                        text: const TextSpan(children: [
                          TextSpan(
                            text: 'Chee',
                            style: TextStyle(
                              color: kAccent,
                              fontSize: 18,
                              fontWeight: FontWeight.w900,
                              letterSpacing: -0.3,
                            ),
                          ),
                          TextSpan(
                            text: 'bo',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w900,
                              letterSpacing: -0.3,
                            ),
                          ),
                        ]),
                      ),
                      const SizedBox(height: 2),
                      const Text(
                        'Assistant Vétérinaire IA',
                        style: TextStyle(
                          color: kTextMuted,
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                ),
                // Online status badge
                AnimatedBuilder(
                  animation: _pulseController,
                  builder: (_, __) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0D3320).withOpacity(0.6),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(
                        color: Colors.greenAccent.withOpacity(
                          0.2 + _pulseController.value * 0.15,
                        ),
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: Colors.greenAccent,
                            boxShadow: [
                              BoxShadow(
                                color: Colors.greenAccent.withOpacity(
                                  0.4 + _pulseController.value * 0.3,
                                ),
                                blurRadius: 4 + _pulseController.value * 2,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(width: 5),
                        const Text(
                          'En ligne',
                          style: TextStyle(
                            color: Colors.greenAccent,
                            fontSize: 10,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // New chat button
                GestureDetector(
                  onTap: _newChat,
                  child: Container(
                    width: 38, height: 38,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const LinearGradient(
                        colors: [kAccent, kPrimary],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      boxShadow: [BoxShadow(color: kPrimary.withOpacity(0.3), blurRadius: 8)],
                    ),
                    child: const Icon(Icons.add_rounded, color: Colors.white, size: 20),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildMessageList() {
    if (_messages.isEmpty && !_isTyping) {
      return _buildEmptyState();
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 70),
      itemCount: _messages.length,
      itemBuilder: (ctx, i) => _buildMessageBubble(_messages[i], i),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: kPrimary.withOpacity(0.1),
              border: Border.all(color: kPrimary.withOpacity(0.2)),
            ),
            child: const Center(
              child: Icon(Icons.pets, size: 36, color: kAccent),
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'Démarrage de la conversation...',
            style: TextStyle(
              color: kTextMuted,
              fontSize: 15,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message, int index) {
    final isUser = message.role == 'user';
    final isEmergency = message.agentType == 'EMERGENCY';
    final isError = message.agentType == 'ERROR';
    final agentLabel = _getAgentLabel(message.agentType);

    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.0, end: 1.0),
      duration: const Duration(milliseconds: 450),
      curve: Curves.easeOutCubic,
      builder: (context, value, child) {
        return Transform.translate(
          offset: Offset(0, 20 * (1 - value)),
          child: Opacity(
            opacity: value,
            child: child,
          ),
        );
      },
      child: Padding(
        padding: const EdgeInsets.only(bottom: 16),
        child: Column(
          crossAxisAlignment:
              isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
          children: [
            // Agent type label
            if (!isUser && agentLabel.isNotEmpty) ...[
              Padding(
                padding: const EdgeInsets.only(left: 44, bottom: 6),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isEmergency
                        ? kAccent.withOpacity(0.12)
                        : isError
                            ? Colors.orange.withOpacity(0.12)
                            : kPrimary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    agentLabel,
                    style: TextStyle(
                      color: isEmergency
                          ? kAccent
                          : isError
                              ? Colors.orangeAccent
                              : kAccent,
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ],
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              mainAxisAlignment:
                  isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
              children: [
                // Agent avatar
                if (!isUser) ...[
                  Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: isEmergency
                          ? const LinearGradient(
                              colors: [Color(0xFF6B1A1A), Color(0xFF4A0E0E)])
                          : const LinearGradient(
                              colors: [kGradientStart, kPrimary]),
                    ),
                    child: Center(
                      child: isEmergency
                          ? const Icon(Icons.emergency_rounded, size: 16, color: Color(0xFFEF4444))
                          : const Icon(Icons.pets, size: 16, color: kAccent),
                    ),
                  ),
                  const SizedBox(width: 8),
                ],
                // Bubble
                Flexible(
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                    decoration: BoxDecoration(
                      gradient: isUser
                          ? const LinearGradient(
                              colors: [kUserBubbleStart, kUserBubbleEnd],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            )
                          : null,
                      color: isUser
                          ? null
                          : isEmergency
                              ? const Color(0xFF2D0A0A)
                              : kBgCardLight,
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(20),
                        topRight: const Radius.circular(20),
                        bottomLeft: isUser
                            ? const Radius.circular(20)
                            : const Radius.circular(4),
                        bottomRight: isUser
                            ? const Radius.circular(4)
                            : const Radius.circular(20),
                      ),
                      border: isEmergency
                          ? Border.all(
                              color: Colors.red.withOpacity(0.3), width: 1)
                          : isUser
                              ? null
                              : Border.all(
                                  color: kPrimary.withOpacity(0.08), width: 0.5),
                      boxShadow: [
                        if (isUser)
                          BoxShadow(
                            color: kPrimary.withOpacity(0.25),
                            blurRadius: 12,
                            offset: const Offset(0, 4),
                          ),
                        if (!isUser)
                          BoxShadow(
                            color: Colors.black.withOpacity(0.15),
                            blurRadius: 8,
                            offset: const Offset(0, 2),
                          ),
                      ],
                    ),
                    child: _buildBubbleContent(message, isUser),
                  ),
                ),
                if (isUser) const SizedBox(width: 4),
              ],
            ),
            // Timestamp
            Padding(
              padding: EdgeInsets.only(
                top: 5,
                left: isUser ? 0 : 44,
                right: isUser ? 4 : 0,
              ),
              child: Text(
                _formatTime(message.timestamp),
                style: const TextStyle(
                  color: Color(0xFF5A4A78),
                  fontSize: 10,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
            // Bouton TTS "Écouter" (uniquement messages agent, pas erreurs)
            if (!isUser && message.agentType != 'ERROR' && message.content.length > 20)
              Padding(
                padding: const EdgeInsets.only(left: 40, top: 2),
                child: _buildTtsButton(message),
              ),
            // Vet cards (si consultation recommandée)
            if (!isUser &&
                message.partnerVets != null &&
                message.partnerVets!.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(left: 40, top: 8),
                child: _buildVetCards(message.partnerVets!),
              ),
          ],
        ),
      ),
    );
  }

  // ── Drawer historique ───────────────────────────────────────────

  Widget _buildDrawer() {
    return Drawer(
      backgroundColor: kBgCard,
      child: SafeArea(
        child: Column(
          children: [
            // En-tête
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 8, 8),
              child: Row(
                children: [
                  const Text('🐾', style: TextStyle(fontSize: 22)),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text('Mes conversations',
                        style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700)),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: kTextMuted, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),
            // Bouton nouveau chat
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              child: GestureDetector(
                onTap: _newChat,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(vertical: 11),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [kAccent, kPrimary]),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.add_rounded, color: Colors.white, size: 18),
                      SizedBox(width: 6),
                      Text('Nouvelle conversation',
                          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
                    ],
                  ),
                ),
              ),
            ),
            const Divider(color: Color(0xFF2D2050), height: 20),
            // Liste des sessions
            Expanded(
              child: _savedSessions.isEmpty
                  ? const Center(
                      child: Text('Aucune conversation sauvegardée',
                          style: TextStyle(color: kTextMuted, fontSize: 12),
                          textAlign: TextAlign.center),
                    )
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 8),
                      itemCount: _savedSessions.length,
                      itemBuilder: (_, i) {
                        final s = _savedSessions[i];
                        final date = DateTime.tryParse(s['date'] ?? '') ?? DateTime.now();
                        final isActive = s['session_id'] == _sessionId;
                        return Container(
                          margin: const EdgeInsets.only(bottom: 4),
                          decoration: BoxDecoration(
                            color: isActive ? kPrimary.withOpacity(0.12) : Colors.transparent,
                            borderRadius: BorderRadius.circular(10),
                            border: isActive ? Border.all(color: kPrimary.withOpacity(0.3)) : null,
                          ),
                          child: ListTile(
                            dense: true,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                            leading: Container(
                              width: 32, height: 32,
                              decoration: BoxDecoration(shape: BoxShape.circle, color: kSurface),
                              child: const Center(child: Icon(Icons.chat_bubble_outline, size: 14, color: kAccent)),
                            ),
                            title: Text(
                              s['title'] ?? 'Conversation',
                              style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w500),
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                            ),
                            subtitle: Text(
                              '${date.day}/${date.month}/${date.year} ${date.hour.toString().padLeft(2,'0')}:${date.minute.toString().padLeft(2,'0')}',
                              style: const TextStyle(color: kTextMuted, fontSize: 10),
                            ),
                            onTap: () => _loadSession(s),
                            trailing: IconButton(
                              icon: const Icon(Icons.delete_outline, color: kTextMuted, size: 16),
                              onPressed: () async {
                                await ApiService.deleteChatSession(s['session_id'] as String);
                                await _loadSavedSessions();
                              },
                            ),
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

  // ── Cartes vétérinaires partenaires ────────────────────────────

  Widget _buildVetCards(List<Map<String, dynamic>> vets) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(bottom: 8),
          child: Text(
            '🏥 Vétérinaires à proximité',
            style: TextStyle(
              color: kAccent,
              fontSize: 11,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.3,
            ),
          ),
        ),

        // Liste des vets avec numéro de téléphone
        ...vets.map((vet) => Container(
          margin: const EdgeInsets.only(bottom: 8),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: kBgCardLight,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: kPrimary.withOpacity(0.2)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      vet['name'] ?? '',
                      style: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                        fontSize: 13,
                      ),
                    ),
                  ),
                  if (vet['distance_km'] != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: kPrimary.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        '📍 ${vet['distance_km']} km',
                        style: const TextStyle(
                          color: kAccent,
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                ],
              ),
              if ((vet['address'] as String?)?.isNotEmpty == true) ...[
                const SizedBox(height: 3),
                Text(
                  vet['address'] as String,
                  style: const TextStyle(color: kTextMuted, fontSize: 11),
                ),
              ],
              const SizedBox(height: 8),
              Row(
                children: [
                  if (vet['emergency'] == true)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 6, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text(
                        '🚨 Urgences 24/7',
                        style: TextStyle(
                          color: Colors.redAccent,
                          fontSize: 10,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  const Spacer(),
                  GestureDetector(
                    onTap: () {
                      final phone = vet['phone'] as String?;
                      if (phone != null && phone.isNotEmpty) {
                        _makePhoneCall(phone);
                      }
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                            colors: [kAccent, kPrimary]),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.phone_rounded,
                              color: Colors.white, size: 13),
                          const SizedBox(width: 4),
                          Text(
                            vet['phone'] ?? '',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        )),
      ],
    );
  }

  Widget _buildBubbleContent(ChatMessage message, bool isUser) {
    final imgs = message.imagesBytes;

    // ── Bulle vidéo ───────────────────────────────────────────────
    if (message.videoName != null) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: Colors.black26,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 36, height: 36,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: const LinearGradient(colors: [kAccent, kPrimary]),
                  ),
                  child: const Icon(Icons.play_arrow_rounded, color: Colors.white, size: 20),
                ),
                const SizedBox(width: 8),
                Flexible(
                  child: Text(
                    message.videoName!,
                    style: const TextStyle(color: kTextBody, fontSize: 12),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
          if (message.content.isNotEmpty) ...[
            const SizedBox(height: 8),
            _buildMessageContent(message.content, isUser),
          ],
        ],
      );
    }

    // ── Bulle image(s) ─────────────────────────────────────────────
    if (imgs != null && imgs.isNotEmpty) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          if (imgs.length == 1)
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.memory(imgs[0], width: 220, fit: BoxFit.cover),
            )
          else
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: imgs.map((b) => ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: Image.memory(b, width: 100, height: 100, fit: BoxFit.cover),
              )).toList(),
            ),
          if (message.content.isNotEmpty) ...[
            const SizedBox(height: 8),
            _buildMessageContent(message.content, isUser),
          ],
        ],
      );
    }

    return _buildMessageContent(message.content, isUser);
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    showModalBottomSheet(
      context: context,
      backgroundColor: kBgCard,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 40, height: 4,
                margin: const EdgeInsets.only(bottom: 16),
                decoration: BoxDecoration(
                  color: kTextMuted.withOpacity(0.3),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const Text(
                'Envoyer un média',
                style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 16),
              _sourceOption(
                icon: Icons.camera_alt_rounded,
                label: 'Prendre une photo',
                onTap: () async {
                  Navigator.pop(context);
                  final xf = await picker.pickImage(source: ImageSource.camera, imageQuality: 80);
                  if (xf != null && mounted) {
                    final bytes = await xf.readAsBytes();
                    setState(() { _pendingImages.add(xf); _pendingImagesBytes.add(bytes); });
                  }
                },
              ),
              const SizedBox(height: 10),
              _sourceOption(
                icon: Icons.photo_library_rounded,
                label: 'Choisir depuis la galerie (multi)',
                onTap: () async {
                  Navigator.pop(context);
                  final picked = await picker.pickMultiImage(imageQuality: 80);
                  if (picked.isNotEmpty && mounted) {
                    final bytesList = await Future.wait(picked.map((f) => f.readAsBytes()));
                    setState(() {
                      _pendingImages.addAll(picked);
                      _pendingImagesBytes.addAll(bytesList);
                      _pendingVideo = null;
                    });
                  }
                },
              ),
              const SizedBox(height: 10),
              _sourceOption(
                icon: Icons.videocam_rounded,
                label: 'Envoyer une vidéo (≤ 60s)',
                onTap: () async {
                  Navigator.pop(context);
                  await _pickVideo();
                },
              ),
              const SizedBox(height: 8),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickVideo() async {
    final picker = ImagePicker();
    final xf = await picker.pickVideo(
      source: ImageSource.gallery,
      maxDuration: const Duration(seconds: 60),
    );
    if (xf != null && mounted) {
      setState(() {
        _pendingVideo = xf;
        // Une vidéo et des images en même temps n'est pas supporté
        _pendingImages.clear();
        _pendingImagesBytes.clear();
      });
    }
  }

  Widget _sourceOption({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
        decoration: BoxDecoration(
          color: kSurface,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: kPrimary.withOpacity(0.25)),
        ),
        child: Row(
          children: [
            Container(
              width: 38, height: 38,
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [kAccent, kPrimary]),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 12),
            Text(label, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }

  Widget _buildMessageContent(String content, bool isUser) {
    // Rendering simplifié du markdown (gras avec **)
    final spans = <TextSpan>[];
    final parts = content.split('**');
    for (int i = 0; i < parts.length; i++) {
      spans.add(TextSpan(
        text: parts[i].replaceAll('_', '').replaceAll('*', ''),
        style: TextStyle(
          fontWeight: i % 2 == 1 ? FontWeight.bold : FontWeight.normal,
          color: isUser ? Colors.white : kTextBody,
          fontSize: 14,
          height: 1.55,
          letterSpacing: 0.1,
        ),
      ));
    }
    return RichText(text: TextSpan(children: spans));
  }

  Widget _buildTypingIndicator() {
    return Padding(
      padding: const EdgeInsets.only(left: 16, bottom: 12, right: 16),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          // Avatar
          Container(
            width: 32,
            height: 32,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(colors: [kGradientStart, kPrimary]),
            ),
            child: const Center(
              child: Text('🐾', style: TextStyle(fontSize: 14)),
            ),
          ),
          const SizedBox(width: 8),
          // Typing bubble with wave animation
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            decoration: BoxDecoration(
              color: kBgCardLight,
              borderRadius: const BorderRadius.only(
                topLeft: Radius.circular(20),
                topRight: Radius.circular(20),
                bottomLeft: Radius.circular(4),
                bottomRight: Radius.circular(20),
              ),
              border: Border.all(color: kPrimary.withOpacity(0.08), width: 0.5),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 6,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: AnimatedBuilder(
              animation: _typingController,
              builder: (_, __) {
                return Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(3, (i) {
                    final delay = i * 0.25;
                    final value = math.sin(
                      (_typingController.value + delay) * math.pi * 2,
                    ).clamp(0.0, 1.0);
                    return Container(
                      width: 8,
                      height: 8,
                      margin: const EdgeInsets.symmetric(horizontal: 2.5),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: kSecondary.withOpacity(0.3 + value * 0.7),
                      ),
                    );
                  }),
                );
              },
            ),
          ),
          const SizedBox(width: 8),
          const Text(
            'Cheebo analyse...',
            style: TextStyle(
              color: kTextMuted,
              fontSize: 11,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
      ),
    );
  }

  List<String> _getSuggestedChips() {
    if (_isTyping || _hasText) return [];
    ChatMessage? lastAgent;
    for (final m in _messages.reversed) {
      if (m.role == 'agent') { lastAgent = m; break; }
    }
    if (lastAgent == null) return [];
    final type    = lastAgent.agentType ?? '';
    final content = lastAgent.content.toLowerCase();

    if (type == 'EMERGENCY') {
      return ['🚫 Il ne respire plus', '🩸 Il saigne abondamment', '😱 Il est inconscient', '✅ J\'ai contacté le vétérinaire'];
    }
    if (type == 'GREETING') {
      return ['🍽️ Ne mange pas', '🤢 Vomissement', '💧 Diarrhée', '😴 Léthargique', '🌡️ Fièvre', '🦴 Boite'];
    }
    if (type == 'QUESTION') {
      if (content.contains('combien de temps') || content.contains('depuis')) {
        return ['⏱️ Depuis ce matin', '📅 Depuis hier', '📆 Depuis 2 jours', '🗓️ Depuis une semaine'];
      }
      if (content.contains('mange') || content.contains('appétit')) {
        return ['❌ Ne mange plus du tout', '⬇️ Mange moins', '✅ Mange normalement', '🚫 Refuse la nourriture'];
      }
      if (content.contains('comportement') || content.contains('actif')) {
        return ['😴 Très léthargique', '🎾 Joue normalement', '😔 Il est abattu', '😰 Il est agité'];
      }
      return ['✅ Oui', '❌ Non', '📋 Un peu', '🤔 Je ne sais pas'];
    }
    if (type == 'ANALYSIS') {
      return ['📈 Ça s\'aggrave', '📋 Symptômes persistent', '📉 C\'est mieux', '❓ Que faire à la maison ?'];
    }
    return [];
  }

  Widget _buildInputBar() {
    final chips = _getSuggestedChips();

    return Container(
      decoration: BoxDecoration(
        color: kBgCard.withOpacity(0.9),
        border: const Border(
          top: BorderSide(color: Color(0xFF2D2050), width: 0.5),
        ),
      ),
      child: ClipRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
          child: SafeArea(
            top: false,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // ── Aperçu vidéo en attente ───────────────────
                if (_pendingVideo != null)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: kSurface,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: kPrimary.withOpacity(0.4)),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 32, height: 32,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: const LinearGradient(colors: [kAccent, kPrimary]),
                            ),
                            child: const Icon(Icons.videocam_rounded, color: Colors.white, size: 16),
                          ),
                          const SizedBox(width: 8),
                          Flexible(
                            child: Text(
                              _pendingVideo!.name,
                              style: const TextStyle(color: kTextBody, fontSize: 12),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 8),
                          GestureDetector(
                            onTap: () => setState(() => _pendingVideo = null),
                            child: const Icon(Icons.close_rounded, color: kTextMuted, size: 16),
                          ),
                        ],
                      ),
                    ),
                  ),
                // ── Aperçu photos en attente ──────────────────
                if (_pendingImagesBytes.isNotEmpty)
                  SizedBox(
                    height: 88,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.fromLTRB(12, 10, 12, 0),
                      itemCount: _pendingImagesBytes.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (_, i) => Stack(
                        children: [
                          ClipRRect(
                            borderRadius: BorderRadius.circular(10),
                            child: Image.memory(
                              _pendingImagesBytes[i],
                              width: 72, height: 72,
                              fit: BoxFit.cover,
                            ),
                          ),
                          Positioned(
                            top: 2, right: 2,
                            child: GestureDetector(
                              onTap: () => setState(() {
                                _pendingImages.removeAt(i);
                                _pendingImagesBytes.removeAt(i);
                              }),
                              child: Container(
                                width: 20, height: 20,
                                decoration: const BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: Colors.black54,
                                ),
                                child: const Icon(Icons.close_rounded, color: Colors.white, size: 12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                // ── Chips de réponse rapide ──────────────────
                if (chips.isNotEmpty)
                  SizedBox(
                    height: 44,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      itemCount: chips.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 8),
                      itemBuilder: (_, i) => GestureDetector(
                        onTap: _isTyping ? null : () => _sendMessage(chips[i]),
                        child: Container(
                          alignment: Alignment.center,
                          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                          decoration: BoxDecoration(
                            color: kSurface,
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(color: kPrimary.withOpacity(0.35)),
                          ),
                          child: Text(
                            chips[i],
                            style: const TextStyle(
                              color: kTextBody,
                              fontSize: 12,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ),
                    ),
                  ),
                // ── Mic / champ texte / envoi ─────────────────
                Padding(
                  padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      // Camera button (always visible)
                      GestureDetector(
                        onTap: _pickImage,
                        child: Container(
                          width: 42,
                          height: 42,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: _pendingImagesBytes.isNotEmpty
                                ? kPrimary.withOpacity(0.25)
                                : kSurface,
                            border: Border.all(
                              color: _pendingImagesBytes.isNotEmpty
                                  ? kPrimary.withOpacity(0.6)
                                  : kPrimary.withOpacity(0.2),
                            ),
                          ),
                          child: Icon(
                            Icons.add_photo_alternate_rounded,
                            color: _pendingImagesBytes.isNotEmpty ? kAccent : kSecondary,
                            size: 20,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Mic button (visible when no text)
                      if (!_hasText)
                        AnimatedBuilder(
                          animation: _pulseController,
                          builder: (_, __) => GestureDetector(
                            onTap: _listen,
                            child: Container(
                              width: 42,
                              height: 42,
                              decoration: BoxDecoration(
                                shape: BoxShape.circle,
                                color: _isListening
                                    ? Colors.redAccent.withOpacity(0.15)
                                    : kSurface,
                                border: Border.all(
                                  color: _isListening
                                      ? Colors.redAccent.withOpacity(
                                          0.4 + _pulseController.value * 0.3)
                                      : kPrimary.withOpacity(0.2),
                                ),
                              ),
                              child: Icon(
                                _isListening ? Icons.mic : Icons.mic_none_rounded,
                                color: _isListening ? Colors.redAccent : kSecondary,
                                size: 20,
                              ),
                            ),
                          ),
                        ),
                      if (!_hasText) const SizedBox(width: 8),
                      // Text field
                      Expanded(
                        child: Container(
                          constraints: const BoxConstraints(maxHeight: 120),
                          decoration: BoxDecoration(
                            color: kSurface,
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(
                              color: _focusNode.hasFocus
                                  ? kPrimary.withOpacity(0.4)
                                  : kPrimary.withOpacity(0.15),
                              width: _focusNode.hasFocus ? 1.5 : 1,
                            ),
                          ),
                          child: TextField(
                            controller: _textController,
                            focusNode: _focusNode,
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 14,
                              height: 1.4,
                            ),
                            maxLines: null,
                            textInputAction: TextInputAction.send,
                            onSubmitted: _isTyping ? null : _sendMessage,
                            onTap: () => setState(() {}),
                            decoration: InputDecoration(
                              hintText: _isListening
                                  ? '🎙️ Écoute en cours...'
                                  : _pendingImagesBytes.isNotEmpty
                                      ? 'Ajouter un message (optionnel)...'
                                      : 'Décrivez les symptômes...',
                              hintStyle: TextStyle(
                                color: _isListening
                                    ? Colors.redAccent.withOpacity(0.6)
                                    : const Color(0xFF6B5A8E),
                                fontSize: 14,
                              ),
                              border: InputBorder.none,
                              contentPadding: const EdgeInsets.symmetric(
                                horizontal: 18,
                                vertical: 12,
                              ),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      // Send button
                      GestureDetector(
                        onTap: _isTyping ? null : () => _sendMessage(_textController.text),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          width: 46,
                          height: 46,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: (_hasText || _pendingImagesBytes.isNotEmpty || _pendingVideo != null)
                                ? const LinearGradient(
                                    colors: [kAccent, kPrimary],
                                    begin: Alignment.topLeft,
                                    end: Alignment.bottomRight,
                                  )
                                : LinearGradient(
                                    colors: [kSurface, kSurface.withOpacity(0.8)],
                                  ),
                            boxShadow: (_hasText || _pendingImagesBytes.isNotEmpty || _pendingVideo != null)
                                ? [BoxShadow(color: kPrimary.withOpacity(0.45), blurRadius: 14, offset: const Offset(0, 4))]
                                : [],
                          ),
                          child: Icon(
                            Icons.send_rounded,
                            color: (_hasText || _pendingImagesBytes.isNotEmpty || _pendingVideo != null) ? Colors.white : kTextMuted,
                            size: 20,
                          ),
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
}

// ─── Ambient Background Painter ──────────────────────────────────────
class _AmbientGlowPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // Top-right purple glow
    final paint1 = Paint()
      ..shader = RadialGradient(
        center: Alignment.topRight,
        radius: 0.8,
        colors: [
          kPrimary.withOpacity(0.06),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint1);

    // Bottom-left accent glow
    final paint2 = Paint()
      ..shader = RadialGradient(
        center: Alignment.bottomLeft,
        radius: 0.9,
        colors: [
          kAccent.withOpacity(0.03),
          Colors.transparent,
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), paint2);
  }

  @override
  bool shouldRepaint(_) => false;
}
