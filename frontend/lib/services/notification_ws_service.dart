import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

class NotificationWsService {
  static const String _wsBase = 'ws://127.0.0.1:8000/api/v1/ws/notifications';

  static final NotificationWsService _instance = NotificationWsService._internal();
  factory NotificationWsService() => _instance;
  NotificationWsService._internal();

  WebSocketChannel? _channel;
  final StreamController<Map<String, dynamic>> _controller =
      StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get stream => _controller.stream;

  void connect() {
    _channel?.sink.close();
    _channel = WebSocketChannel.connect(Uri.parse(_wsBase));
    _channel!.stream.listen(
      (data) {
        if (_controller.isClosed) return;
        try {
          final msg = jsonDecode(data as String) as Map<String, dynamic>;
          _controller.add(msg);
        } catch (_) {}
      },
      onDone: () => _channel = null,
      onError: (_) => _channel = null,
    );
  }

  void disconnect() {
    _channel?.sink.close();
    _channel = null;
  }

  void dispose() {
    disconnect();
    _controller.close();
  }
}
