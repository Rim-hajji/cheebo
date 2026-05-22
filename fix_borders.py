import re, os, sys

screens = r"C:\Users\nesrin\Desktop\module_docto_agent\frontend\lib\screens"
files = [
    "dashboard_screen.dart", "chat_screen.dart", "history_screen.dart",
    "articles_screen.dart", "medications_screen.dart", "results_screen.dart",
    "emergency_screen.dart", "settings_screen.dart",
]

# Match BorderSide(...) allowing one level of nested parens e.g. withOpacity(0.1)
bsp = r'BorderSide\((?:[^()]+|\([^)]*\))*\)'

# 4-sided pattern (any order of top/left/bottom/right)
pat4 = re.compile(
    r'border:\s+Border\(\s+(?:top|left|bottom|right):\s+' + bsp +
    r',\s+(?:top|left|bottom|right):\s+' + bsp +
    r',\s+(?:top|left|bottom|right):\s+' + bsp +
    r',\s+(?:top|left|bottom|right):\s+' + bsp +
    r',\s+\)',
    re.DOTALL
)

# 2-sided pattern
pat2 = re.compile(
    r'border:\s+Border\(\s+(?:top|left|bottom|right):\s+' + bsp +
    r',\s+(?:top|left|bottom|right):\s+' + bsp +
    r',\s+\)',
    re.DOTALL
)

# Single-line 1-sided left accent with borderRadius → we'll handle specially
# border: Border(left: BorderSide(color: X, width: Y))
pat1_left = re.compile(
    r'border: Border\(left:\s+' + bsp + r'\)',
)

total = 0
for fname in files:
    path = os.path.join(screens, fname)
    if not os.path.exists(path):
        print(f"SKIP {fname}")
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    m4 = len(pat4.findall(content))
    m2 = len(pat2.findall(content))
    m1 = len(pat1_left.findall(content))

    content = pat4.sub('border: Border.all(color: Colors.white.withOpacity(0.10), width: 0.8)', content)
    content = pat2.sub('border: Border.all(color: Colors.white.withOpacity(0.10), width: 0.8)', content)
    # For single-sided left accent borders combined with borderRadius → remove border, will be handled by shadow
    content = pat1_left.sub('border: Border.all(color: Colors.white.withOpacity(0.08), width: 0.8)', content)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"{fname}: fixed 4={m4} 2={m2} 1left={m1}")
    total += m4 + m2 + m1

print(f"\nTotal fixed: {total}")
