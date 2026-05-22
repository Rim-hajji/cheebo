import 'dart:io';

void main() {
  final dir = r'C:\Users\nesrin\Desktop\module_docto_agent\frontend\lib\screens';
  final files = [
    'dashboard_screen.dart', 'chat_screen.dart', 'history_screen.dart',
    'articles_screen.dart', 'medications_screen.dart', 'results_screen.dart',
    'emergency_screen.dart', 'settings_screen.dart',
  ];

  // BorderSide pattern: allows one level of nested parens (e.g. withOpacity(0.1))
  const bsp = r'BorderSide\((?:[^()]+|\([^)]*\))*\)';
  const side = r'(?:top|left|bottom|right):\s+' + bsp + r',';

  final pat4 = RegExp(
    r'border:\s+Border\(\s+' + side + r'\s+' + side + r'\s+' + side + r'\s+' + side + r'\s+\)',
    dotAll: true,
  );
  final pat2 = RegExp(
    r'border:\s+Border\(\s+' + side + r'\s+' + side + r'\s+\)',
    dotAll: true,
  );
  final pat1 = RegExp(
    r'border:\s+Border\(\s*(?:top|left|bottom|right):\s+' + bsp + r'\s*\)',
    dotAll: true,
  );

  int total = 0;
  for (final fname in files) {
    final path = '$dir\\$fname';
    final f = File(path);
    if (!f.existsSync()) { print('SKIP $fname'); continue; }

    var content = f.readAsStringSync();
    int m4 = pat4.allMatches(content).length;
    int m2 = pat2.allMatches(content).length;
    // After replacing pat4, pat2, check pat1 for remaining
    content = content.replaceAll(pat4, 'border: Border.all(color: Colors.white.withOpacity(0.10), width: 0.8)');
    content = content.replaceAll(pat2, 'border: Border.all(color: Colors.white.withOpacity(0.10), width: 0.8)');
    int m1 = pat1.allMatches(content).length;
    content = content.replaceAll(pat1, 'border: Border.all(color: Colors.white.withOpacity(0.10), width: 0.8)');

    f.writeAsStringSync(content);
    print('$fname: 4-sided=$m4 2-sided=$m2 1-sided=$m1');
    total += m4 + m2 + m1;
  }
  print('\nTotal fixed: $total');
}
