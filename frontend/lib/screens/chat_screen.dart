import 'dart:convert';
import 'dart:math' as math;
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import '../services/api_service.dart';

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

  ChatMessage({
    required this.role,
    required this.content,
    this.agentType,
    this.partnerVets,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with TickerProviderStateMixin {
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
  bool _hasText = false;
  late stt.SpeechToText _speech;
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

    // Déclencher le message de bienvenue au démarrage
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _startConversation();
      _loadSavedSessions();
    });
  }

  @override
  void dispose() {
    _typingController.dispose();
    _pulseController.dispose();
    _sendButtonController.dispose();
    _textController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  Future<void> _startConversation() async {
    setState(() => _isTyping = true);
    await Future.delayed(const Duration(milliseconds: 800));
    try {
      final resp = await ApiService.sendChatMessage(
        message: "",
        sessionId: null,
        history: [],
      );
      _sessionId = resp['session_id'];
      _addAgentMessage(resp['response'] ?? '', resp['agent_type']);
    } catch (_) {
      _addAgentMessage(
          "🐾 Bonjour ! Je suis Cheebo, votre assistant vétérinaire IA. Comment va votre compagnon aujourd'hui ?",
          "GREETING");
    }
    if (mounted) setState(() => _isTyping = false);
  }

  void _addAgentMessage(String content, String? type,
      {List<Map<String, dynamic>>? vets}) {
    setState(() {
      _messages.add(ChatMessage(
        role: 'agent',
        content: content,
        agentType: type,
        partnerVets: vets,
      ));
    });
    Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);
  }

  // ── Session management ──────────────────────────────────────────

  Future<void> _loadSavedSessions() async {
    final sessions = await ApiService.getChatSessions();
    if (mounted) setState(() => _savedSessions = sessions);
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
    _startConversation();
  }

  void _loadSession(Map<String, dynamic> session) {
    if (Navigator.canPop(context)) Navigator.pop(context);
    final rawMsgs = session['messages'] as List<dynamic>? ?? [];
    final messages = rawMsgs.map((m) {
      final vetsRaw = m['partnerVets'] as List<dynamic>?;
      final vets = vetsRaw?.map((v) => Map<String, dynamic>.from(v as Map)).toList();
      final ts = DateTime.tryParse(m['timestamp'] ?? '') ?? DateTime.now();
      return ChatMessage(
        role: m['role'] as String,
        content: m['content'] as String,
        agentType: m['agentType'] as String?,
        partnerVets: vets,
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
    if (text.trim().isEmpty) return;
    _textController.clear();
    _focusNode.requestFocus();

    // Ajouter le message utilisateur
    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text));
      _isTyping = true;
    });
    Future.delayed(const Duration(milliseconds: 100), _scrollToBottom);

    try {
      final historyForApi = _messages
          .map((m) => {'role': m.role, 'content': m.content})
          .toList();
      final resp = await ApiService.sendChatMessage(
        message: text,
        sessionId: _sessionId,
        history: historyForApi,
      );
      _sessionId = resp['session_id'];
      final agentContent = resp['response'] ?? '';
      final agentType = resp['agent_type'];
      final rawVets = resp['partner_vets'] as List<dynamic>?;
      final vets = rawVets
          ?.map((v) => Map<String, dynamic>.from(v as Map))
          .toList();
      if (mounted) {
        setState(() => _isTyping = false);
        _addAgentMessage(agentContent, agentType, vets: vets);
        _saveCurrentSession();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isTyping = false);
        _addAgentMessage(
            "😔 Erreur de connexion. Vérifiez que le serveur est démarré.",
            "ERROR");
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
      body: Stack(
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
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
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
              child: Text('🐾', style: TextStyle(fontSize: 36)),
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
                        ? Colors.red.withOpacity(0.12)
                        : isError
                            ? Colors.orange.withOpacity(0.12)
                            : kPrimary.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    agentLabel,
                    style: TextStyle(
                      color: isEmergency
                          ? Colors.redAccent
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
                      child: Text(
                        isEmergency ? '🚨' : '🐾',
                        style: const TextStyle(fontSize: 14),
                      ),
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
                    child: _buildMessageContent(message.content, isUser),
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
                              child: const Center(child: Text('💬', style: TextStyle(fontSize: 14))),
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
          child: Text('🏥 Vétérinaires partenaires Cheebo',
              style: TextStyle(color: kAccent, fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.3)),
        ),
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
              Text(vet['name'] ?? '',
                  style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13)),
              const SizedBox(height: 3),
              Text(vet['address'] ?? '',
                  style: const TextStyle(color: kTextMuted, fontSize: 11)),
              const SizedBox(height: 8),
              Row(
                children: [
                  if (vet['emergency'] == true)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.red.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Text('🚨 Urgences 24/7',
                          style: TextStyle(color: Colors.redAccent, fontSize: 10, fontWeight: FontWeight.w600)),
                    ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [kAccent, kPrimary]),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.phone_rounded, color: Colors.white, size: 13),
                        const SizedBox(width: 4),
                        Text(vet['phone'] ?? '',
                            style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w600)),
                      ],
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

  Widget _buildInputBar() {
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
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  // Mic button
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
                        onSubmitted: _sendMessage,
                        onTap: () => setState(() {}),
                        decoration: InputDecoration(
                          hintText: _isListening
                              ? '🎙️ Écoute en cours...'
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
                    onTap: () => _sendMessage(_textController.text),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      width: 46,
                      height: 46,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: _hasText
                            ? const LinearGradient(
                                colors: [kAccent, kPrimary],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              )
                            : LinearGradient(
                                colors: [
                                  kSurface,
                                  kSurface.withOpacity(0.8),
                                ],
                              ),
                        boxShadow: _hasText
                            ? [
                                BoxShadow(
                                  color: kPrimary.withOpacity(0.45),
                                  blurRadius: 14,
                                  offset: const Offset(0, 4),
                                ),
                              ]
                            : [],
                      ),
                      child: Icon(
                        Icons.send_rounded,
                        color: _hasText ? Colors.white : kTextMuted,
                        size: 20,
                      ),
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
