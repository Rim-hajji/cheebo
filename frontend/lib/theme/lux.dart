import 'dart:ui';
import 'package:flutter/material.dart';

// ══════════════════════════════════════════════════════════════════════
//  CHEEBO LUXURY DESIGN SYSTEM
// ══════════════════════════════════════════════════════════════════════

// ── Palette ───────────────────────────────────────────────────────────
const kBg       = Color(0xFF04020F);   // deep space
const kBgCard   = Color(0xFF0C0820);   // card surface
const kBgCardL  = Color(0xFF130B28);   // lighter card
const kBorder   = Color(0xFF1E1340);   // subtle border

const kGold     = Color(0xFFD4A853);   // premium gold
const kGoldL    = Color(0xFFF0C96A);   // light gold
const kGoldD    = Color(0xFF9B7A2E);   // dark gold

const kPrimary  = Color(0xFF7C3AED);   // violet primary
const kAccent   = Color(0xFF9D5CF6);   // violet accent
const kAccent2  = Color(0xFFBD8FF8);   // soft violet

const kRose     = Color(0xFFDB2777);   // rose
const kRoseL    = Color(0xFFF472B6);   // light rose
const kRoseD    = Color(0xFFA81E5F);   // dark rose
const kEmerald  = Color(0xFF10B981);   // emerald
const kAmber    = Color(0xFFF59E0B);   // amber
const kRed      = Color(0xFFEF4444);   // red

const kText     = Color(0xFFF0EEF8);   // near white
const kBody     = Color(0xFFCDC4E8);   // body text
const kMuted    = Color(0xFF5A5070);   // muted

// ── Gradients ─────────────────────────────────────────────────────────
const gradPrimary = LinearGradient(colors: [kAccent2, kPrimary], begin: Alignment.topLeft, end: Alignment.bottomRight);
const gradGold    = LinearGradient(colors: [kGoldL, kGold, kGoldD], begin: Alignment.topLeft, end: Alignment.bottomRight);
const gradRose    = LinearGradient(colors: [Color(0xFFEC4899), kRose], begin: Alignment.topLeft, end: Alignment.bottomRight);
const gradEmerald = LinearGradient(colors: [Color(0xFF34D399), kEmerald], begin: Alignment.topLeft, end: Alignment.bottomRight);
const gradBg      = LinearGradient(colors: [Color(0xFF0A0520), kBg], begin: Alignment.topCenter, end: Alignment.bottomCenter);

// ── Glass Card ────────────────────────────────────────────────────────
class LuxCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double radius;
  final Color? borderColor;
  final Color? glowColor;
  final double? width;
  final Gradient? gradient;
  final VoidCallback? onTap;

  const LuxCard({
    super.key,
    required this.child,
    this.padding,
    this.margin,
    this.radius = 20,
    this.borderColor,
    this.glowColor,
    this.width,
    this.gradient,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: width,
      margin: margin,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: gradient,
        boxShadow: [
          if (glowColor != null)
            BoxShadow(color: glowColor!.withOpacity(0.18), blurRadius: 24, spreadRadius: 0, offset: const Offset(0, 4)),
          BoxShadow(color: Colors.black.withOpacity(0.35), blurRadius: 16, offset: const Offset(0, 4)),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(radius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
          child: Container(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(radius),
              gradient: gradient ?? LinearGradient(
                colors: [kBgCardL.withOpacity(0.9), kBgCard.withOpacity(0.85)],
                begin: Alignment.topLeft, end: Alignment.bottomRight,
              ),
              border: Border.all(
                color: borderColor ?? kBorder.withOpacity(0.8),
                width: 0.8,
              ),
            ),
            child: Material(
              color: Colors.transparent,
              child: onTap != null
                  ? InkWell(
                      onTap: onTap,
                      borderRadius: BorderRadius.circular(radius),
                      splashColor: kPrimary.withOpacity(0.05),
                      child: Padding(padding: padding ?? EdgeInsets.zero, child: child),
                    )
                  : Padding(padding: padding ?? EdgeInsets.zero, child: child),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Gradient Border ───────────────────────────────────────────────────
class GradientBorderCard extends StatelessWidget {
  final Widget child;
  final Gradient borderGradient;
  final EdgeInsetsGeometry? padding;
  final EdgeInsetsGeometry? margin;
  final double radius;
  final double borderWidth;
  final Color fillColor;

  const GradientBorderCard({
    super.key,
    required this.child,
    this.borderGradient = gradGold,
    this.padding,
    this.margin,
    this.radius = 20,
    this.borderWidth = 1.2,
    this.fillColor = kBgCard,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: borderGradient,
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.3), blurRadius: 12, offset: const Offset(0, 4))],
      ),
      child: Container(
        margin: EdgeInsets.all(borderWidth),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(radius - borderWidth),
          color: fillColor,
        ),
        child: Padding(padding: padding ?? EdgeInsets.zero, child: child),
      ),
    );
  }
}

// ── Gradient Text ─────────────────────────────────────────────────────
class GradText extends StatelessWidget {
  final String text;
  final TextStyle style;
  final Gradient gradient;

  const GradText(this.text, {super.key, required this.style, this.gradient = gradGold});

  @override
  Widget build(BuildContext context) {
    return ShaderMask(
      shaderCallback: (bounds) => gradient.createShader(bounds),
      blendMode: BlendMode.srcIn,
      child: Text(text, style: style),
    );
  }
}

// ── Glow Container ────────────────────────────────────────────────────
class GlowBox extends StatelessWidget {
  final Widget child;
  final Color color;
  final double blurRadius;
  final double spread;

  const GlowBox({super.key, required this.child, required this.color, this.blurRadius = 20, this.spread = 0});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: [BoxShadow(color: color.withOpacity(0.4), blurRadius: blurRadius, spreadRadius: spread)],
      ),
      child: child,
    );
  }
}

// ── Section Header ────────────────────────────────────────────────────
class LuxSection extends StatelessWidget {
  final String title;
  final IconData? icon;
  final Widget? trailing;

  const LuxSection(this.title, {super.key, this.icon, this.trailing});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      if (icon != null) ...[
        ShaderMask(
          shaderCallback: (b) => gradGold.createShader(b),
          blendMode: BlendMode.srcIn,
          child: Icon(icon, size: 15),
        ),
        const SizedBox(width: 8),
      ],
      Text(title, style: const TextStyle(
        color: kText, fontSize: 14, fontWeight: FontWeight.w700, letterSpacing: 0.5)),
      const Spacer(),
      if (trailing != null) trailing!,
    ]);
  }
}

// ── Luxury Chip ───────────────────────────────────────────────────────
class LuxChip extends StatelessWidget {
  final String text;
  final Color? color;
  final IconData? icon;
  final bool gold;

  const LuxChip(this.text, {super.key, this.color, this.icon, this.gold = false});

  @override
  Widget build(BuildContext context) {
    final c = color ?? (gold ? kGold : kAccent);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: c.withOpacity(0.3)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        if (icon != null) ...[Icon(icon, color: c, size: 11), const SizedBox(width: 4)],
        Text(text, style: TextStyle(color: c, fontSize: 10, fontWeight: FontWeight.w700, letterSpacing: 0.3)),
      ]),
    );
  }
}

// ── Luxury Divider ────────────────────────────────────────────────────
class LuxDivider extends StatelessWidget {
  const LuxDivider({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 0.6,
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Colors.transparent, kBorder, kGoldD, kBorder, Colors.transparent],
        ),
      ),
    );
  }
}

// ── Ambient Background ────────────────────────────────────────────────
class LuxBackground extends StatelessWidget {
  final Widget child;
  const LuxBackground({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Stack(children: [
      Positioned.fill(child: CustomPaint(painter: _LuxBgPainter())),
      child,
    ]);
  }
}

class _LuxBgPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    void glow(Alignment align, Color color, double radius) {
      final center = Offset(
        (align.x + 1) / 2 * size.width,
        (align.y + 1) / 2 * size.height,
      );
      final paint = Paint()
        ..shader = RadialGradient(colors: [color.withOpacity(0.09), Colors.transparent], radius: 0.6)
            .createShader(Rect.fromCircle(center: center, radius: radius));
      canvas.drawCircle(center, radius, paint);
    }

    glow(const Alignment(-0.6, -0.8), kPrimary,    size.width * 0.7);
    glow(const Alignment(0.8, 0.2),   kGold,       size.width * 0.45);
    glow(const Alignment(-0.2, 0.9),  kRose,       size.width * 0.4);
    glow(const Alignment(0.4, -0.5),  kAccent,     size.width * 0.35);
  }

  @override
  bool shouldRepaint(_) => false;
}
