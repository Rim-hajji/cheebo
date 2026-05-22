import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

class WsService {
  //static const String _wsBase = 'ws://192.168.1.14:8000/api/v1/ws/chat';
   static const String _wsBase = 'ws://127.0.0.1:8000/api/v1/ws/chat';

  WebSocketChannel? _channel;
  final StreamController<Map<String, dynamic>> _controller =
      StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get stream => _controller.stream;
  bool get isConnected => _channel != null;

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
      onDone: () {
        _channel = null;
        if (!_controller.isClosed) _controller.add({'type': 'disconnected'});
      },
      onError: (e) {
        _channel = null;
        if (!_controller.isClosed) _controller.add({'type': 'connection_error', 'message': e.toString()});
      },
    );
  }

  void sendMessage({required String message}) {
    if (_channel == null) return;
    _channel!.sink.add(jsonEncode({'message': message}));
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
