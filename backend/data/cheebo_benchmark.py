#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cheebo_benchmark.py
====================
Évaluation quantitative du modèle Cheebo multi-tâches fine-tuné.

Métriques par tâche :
  T1 — ROUGE-1/2/L + taux disclaimer + taux urgence correcte
  T2 — JSON validity % + précision animal + précision urgency_hint
  T3 — JSON validity % + précision urgency + précision condition clé
  T4 — JSON validity % + précision vet_needed + précision home_care_ok
  T5 — JSON validity % + précision valid/invalid + précision correction urgence

Usage Google Colab (après entraînement) :
    exec(open('cheebo_benchmark.py').read())
"""

import json, re, time, warnings
from collections import defaultdict

import torch
warnings.filterwarnings("ignore")

# ── Détection automatique CPU / GPU ───────────────────────────────────────────
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"GPU disponible : {torch.cuda.is_available()}")
print(f"Device utilisé : {DEVICE}")
if DEVICE == "cpu":
    print("⚠️  Mode CPU — inférence lente. N_PER_TASK sera réduit à 5 automatiquement.")

# ── Chargement du modèle en mode inférence ────────────────────────────────────
from unsloth import FastLanguageModel
FastLanguageModel.for_inference(model)

ALPACA = "### Instruction:\n{}\n\n### Input:\n{}\n\n### Response:\n"

def generate(instruction, input_text, max_tokens=400, temperature=0.1):
    """Génère une réponse et retourne uniquement la partie Response."""
    prompt  = ALPACA.format(instruction, input_text)
    inputs  = tokenizer(prompt, return_tensors="pt").to(DEVICE)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out = model.generate(
            **inputs,
            max_new_tokens = max_tokens,
            temperature    = temperature,
            do_sample      = temperature > 0,
            use_cache      = True,
        )
    decoded = tokenizer.decode(out[0], skip_special_tokens=True)
    return decoded.split("### Response:")[-1].strip()

# ── Utilitaires ───────────────────────────────────────────────────────────────

def try_parse_json(text):
    """Tente de parser le JSON — retourne dict ou None."""
    text = text.strip()
    # Nettoyer blocs markdown
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(text)
    except Exception:
        # Essai avec raw_decode
        start = text.find("{")
        if start != -1:
            try:
                obj, _ = json.JSONDecoder().raw_decode(text[start:])
                return obj
            except Exception:
                pass
    return None

def normalize_urgency(lvl):
    """Normalise les variantes de niveau d'urgence."""
    if not lvl:
        return "UNKNOWN"
    lvl = str(lvl).upper()
    if any(x in lvl for x in ["CRITIQUE", "CRITICAL", "CRIT"]):
        return "CRITICAL"
    if any(x in lvl for x in ["ÉLEVÉ", "ELEVE", "HIGH"]):
        return "HIGH"
    if any(x in lvl for x in ["MODÉRÉ", "MODERE", "MODERATE", "MOYEN"]):
        return "MODERATE"
    if any(x in lvl for x in ["FAIBLE", "LOW", "BAS"]):
        return "LOW"
    return "UNKNOWN"

def rouge_scores(reference, hypothesis):
    """ROUGE-1/2/L simplifié (word-level)."""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    if not ref_tokens or not hyp_tokens:
        return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

    # ROUGE-1
    ref_1 = set(ref_tokens)
    hyp_1 = set(hyp_tokens)
    r1_p  = len(ref_1 & hyp_1) / len(hyp_1) if hyp_1 else 0
    r1_r  = len(ref_1 & hyp_1) / len(ref_1) if ref_1 else 0
    r1_f  = (2 * r1_p * r1_r / (r1_p + r1_r)) if (r1_p + r1_r) > 0 else 0

    # ROUGE-2
    def bigrams(tokens):
        return set(zip(tokens, tokens[1:]))
    ref_2 = bigrams(ref_tokens)
    hyp_2 = bigrams(hyp_tokens)
    r2_p  = len(ref_2 & hyp_2) / len(hyp_2) if hyp_2 else 0
    r2_r  = len(ref_2 & hyp_2) / len(ref_2) if ref_2 else 0
    r2_f  = (2 * r2_p * r2_r / (r2_p + r2_r)) if (r2_p + r2_r) > 0 else 0

    # ROUGE-L (LCS approximé)
    def lcs_len(a, b):
        m, n = len(a), len(b)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dp[i][j] = dp[i-1][j-1] + 1 if a[i-1] == b[j-1] else max(dp[i-1][j], dp[i][j-1])
        return dp[m][n]
    lcs   = lcs_len(ref_tokens[:50], hyp_tokens[:50])  # tronqué pour performance
    rl_p  = lcs / len(hyp_tokens) if hyp_tokens else 0
    rl_r  = lcs / len(ref_tokens) if ref_tokens else 0
    rl_f  = (2 * rl_p * rl_r / (rl_p + rl_r)) if (rl_p + rl_r) > 0 else 0

    return {"rouge1": round(r1_f, 4), "rouge2": round(r2_f, 4), "rougeL": round(rl_f, 4)}

# ══════════════════════════════════════════════════════════════════════════════
#  BENCHMARK PAR TÂCHE
# ══════════════════════════════════════════════════════════════════════════════

def benchmark_task(task_id, samples, verbose=False):
    """Évalue un ensemble d'exemples pour une tâche donnée."""
    results = []
    latencies = []

    for ex in samples:
        t0   = time.time()
        pred = generate(ex["instruction"], ex["input"])
        lat  = round((time.time() - t0) * 1000, 1)
        latencies.append(lat)

        ref  = ex["output"]
        r    = {"pred": pred, "ref": ref, "latency_ms": lat}

        if task_id == "T1":
            # Métriques textuelles
            r["rouge"]      = rouge_scores(ref, pred)
            r["disclaimer"] = "_Ces conseils" in pred or "_These recommendations" in pred
            r["has_emoji"]  = any(e in pred for e in ["🚨", "⚠️", "📋", "✅"])
            # Urgence dans la réponse
            urgency_in_pred = normalize_urgency(re.search(
                r"(CRITIQUE|CRITICAL|ÉLEVÉ|HIGH|MODÉRÉ|MODERATE|FAIBLE|LOW)",
                pred, re.IGNORECASE
            ).group(0) if re.search(r"(CRITIQUE|CRITICAL|ÉLEVÉ|HIGH|MODÉRÉ|MODERATE|FAIBLE|LOW)", pred, re.IGNORECASE) else "")
            urgency_in_ref  = normalize_urgency(re.search(
                r"(CRITIQUE|CRITICAL|ÉLEVÉ|HIGH|MODÉRÉ|MODERATE|FAIBLE|LOW)",
                ref, re.IGNORECASE
            ).group(0) if re.search(r"(CRITIQUE|CRITICAL|ÉLEVÉ|HIGH|MODÉRÉ|MODERATE|FAIBLE|LOW)", ref, re.IGNORECASE) else "")
            r["urgency_ok"] = urgency_in_pred == urgency_in_ref

        else:
            # Métriques JSON (T2-T5)
            pred_json = try_parse_json(pred)
            ref_json  = try_parse_json(ref) if isinstance(ref, str) else ref
            r["json_valid"] = pred_json is not None

            if pred_json and ref_json:
                if task_id == "T2":
                    r["animal_ok"]   = pred_json.get("animal","").lower() == ref_json.get("animal","").lower()
                    r["urgency_ok"]  = normalize_urgency(pred_json.get("urgency_hint","")) == normalize_urgency(ref_json.get("urgency_hint",""))
                    pred_syms = set(s.lower() for s in pred_json.get("symptoms_normalized", []))
                    ref_syms  = set(s.lower() for s in ref_json.get("symptoms_normalized", []))
                    r["symptoms_overlap"] = len(pred_syms & ref_syms) / max(len(ref_syms), 1)

                elif task_id == "T3":
                    r["urgency_ok"]  = normalize_urgency(
                        pred_json.get("possible_associations", [{}])[0].get("urgency_hint","")
                    ) == normalize_urgency(
                        ref_json.get("possible_associations", [{}])[0].get("urgency_hint","")
                    )
                    r["has_concern"] = bool(pred_json.get("main_concern",""))
                    r["has_delay"]   = bool(pred_json.get("watch_delay",""))
                    r["n_conditions"] = len(pred_json.get("possible_associations", []))

                elif task_id == "T4":
                    r["vet_needed_ok"]   = pred_json.get("vet_needed") == ref_json.get("vet_needed")
                    r["home_care_ok"]    = pred_json.get("home_care_ok") == ref_json.get("home_care_ok")
                    r["has_care_steps"]  = len(pred_json.get("immediate_care", [])) > 0
                    r["has_emerg_signs"] = len(pred_json.get("emergency_signs", [])) > 0

                elif task_id == "T5":
                    r["valid_ok"]     = pred_json.get("valid") == ref_json.get("valid")
                    r["urgency_ok"]   = normalize_urgency(pred_json.get("corrected_urgency","")) == normalize_urgency(ref_json.get("corrected_urgency",""))
                    r["has_reason"]   = bool(pred_json.get("reason",""))
                    r["confidence_ok"] = 0.5 <= float(pred_json.get("confidence", 0)) <= 1.0

        if verbose:
            print(f"  [{task_id}] lat={lat}ms | {dict(list(r.items())[-3:])}")
        results.append(r)

    return results, latencies

# ══════════════════════════════════════════════════════════════════════════════
#  SÉLECTION DES ÉCHANTILLONS DEPUIS LE TEST SET
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("  CHEEBO MULTI-TASK BENCHMARK")
print("=" * 60)

# Séparer le test_dataset par tâche
task_samples = defaultdict(list)
for ex in test_dataset:
    instr = ex["instruction"]
    if "Cheebo, assistant vétérinaire" in instr and "JSON" not in instr:
        task_samples["T1"].append(ex)
    elif "normalisation" in instr.lower():
        task_samples["T2"].append(ex)
    elif "prédiction" in instr.lower():
        task_samples["T3"].append(ex)
    elif "recommandations" in instr.lower():
        task_samples["T4"].append(ex)
    elif "validation médicale" in instr.lower():
        task_samples["T5"].append(ex)

# Limiter à N exemples par tâche (réduit auto sur CPU)
N_PER_TASK = 5 if DEVICE == "cpu" else 20
selected = {k: v[:N_PER_TASK] for k, v in task_samples.items()}
total_samples = sum(len(v) for v in selected.values())
print(f"\nÉchantillons évalués : {total_samples} ({N_PER_TASK}/tâche × 5 tâches)\n")

# ══════════════════════════════════════════════════════════════════════════════
#  EXÉCUTION DU BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════

all_results = {}
all_latencies = []

for task_id in ["T1", "T2", "T3", "T4", "T5"]:
    samples = selected.get(task_id, [])
    if not samples:
        print(f"  {task_id}: aucun exemple dans le test set pour cette tâche")
        continue
    print(f"Évaluation {task_id} ({len(samples)} exemples)...", end=" ", flush=True)
    t_start = time.time()
    results, latencies = benchmark_task(task_id, samples)
    t_total = round(time.time() - t_start, 1)
    all_results[task_id] = results
    all_latencies.extend(latencies)
    print(f"✅ ({t_total}s)")

# ══════════════════════════════════════════════════════════════════════════════
#  RAPPORT FINAL
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("  RÉSULTATS DÉTAILLÉS")
print("=" * 60)

summary = {}

# ── T1 ────────────────────────────────────────────────────────────────────────
if "T1" in all_results:
    rs = all_results["T1"]
    n  = len(rs)
    avg_r1  = round(sum(r["rouge"]["rouge1"] for r in rs) / n, 4)
    avg_r2  = round(sum(r["rouge"]["rouge2"] for r in rs) / n, 4)
    avg_rl  = round(sum(r["rouge"]["rougeL"] for r in rs) / n, 4)
    disc_rt = round(sum(r["disclaimer"] for r in rs) / n * 100, 1)
    emj_rt  = round(sum(r["has_emoji"] for r in rs) / n * 100, 1)
    urg_rt  = round(sum(r.get("urgency_ok", False) for r in rs) / n * 100, 1)
    avg_lat = round(sum(r["latency_ms"] for r in rs) / n)
    print(f"\n📝 T1 — Réponse vétérinaire ({n} exemples)")
    print(f"   ROUGE-1     : {avg_r1:.4f}")
    print(f"   ROUGE-2     : {avg_r2:.4f}")
    print(f"   ROUGE-L     : {avg_rl:.4f}")
    print(f"   Disclaimer  : {disc_rt}%")
    print(f"   Emoji urgence: {emj_rt}%")
    print(f"   Urgence OK  : {urg_rt}%")
    print(f"   Latence moy : {avg_lat}ms")
    summary["T1"] = {"rouge1": avg_r1, "rouge2": avg_r2, "rougeL": avg_rl,
                     "disclaimer%": disc_rt, "urgency_acc%": urg_rt, "latency_ms": avg_lat}

# ── T2 ────────────────────────────────────────────────────────────────────────
if "T2" in all_results:
    rs = all_results["T2"]
    n  = len(rs)
    json_rt  = round(sum(r.get("json_valid", False) for r in rs) / n * 100, 1)
    anim_rt  = round(sum(r.get("animal_ok", False) for r in rs) / n * 100, 1)
    urg_rt   = round(sum(r.get("urgency_ok", False) for r in rs) / n * 100, 1)
    sym_ov   = round(sum(r.get("symptoms_overlap", 0) for r in rs) / n * 100, 1)
    avg_lat  = round(sum(r["latency_ms"] for r in rs) / n)
    print(f"\n🔍 T2 — Normalisation symptômes ({n} exemples)")
    print(f"   JSON valide    : {json_rt}%")
    print(f"   Animal correct : {anim_rt}%")
    print(f"   Urgence OK     : {urg_rt}%")
    print(f"   Overlap symptômes: {sym_ov}%")
    print(f"   Latence moy    : {avg_lat}ms")
    summary["T2"] = {"json_valid%": json_rt, "animal_acc%": anim_rt,
                     "urgency_acc%": urg_rt, "symptoms_overlap%": sym_ov, "latency_ms": avg_lat}

# ── T3 ────────────────────────────────────────────────────────────────────────
if "T3" in all_results:
    rs = all_results["T3"]
    n  = len(rs)
    json_rt  = round(sum(r.get("json_valid", False) for r in rs) / n * 100, 1)
    urg_rt   = round(sum(r.get("urgency_ok", False) for r in rs) / n * 100, 1)
    conc_rt  = round(sum(r.get("has_concern", False) for r in rs) / n * 100, 1)
    delay_rt = round(sum(r.get("has_delay", False) for r in rs) / n * 100, 1)
    avg_cond = round(sum(r.get("n_conditions", 0) for r in rs) / n, 1)
    avg_lat  = round(sum(r["latency_ms"] for r in rs) / n)
    print(f"\n🧠 T3 — Prédiction conditions ({n} exemples)")
    print(f"   JSON valide      : {json_rt}%")
    print(f"   Urgence OK       : {urg_rt}%")
    print(f"   Concern présent  : {conc_rt}%")
    print(f"   Watch delay      : {delay_rt}%")
    print(f"   Conditions/réponse: {avg_cond}")
    print(f"   Latence moy      : {avg_lat}ms")
    summary["T3"] = {"json_valid%": json_rt, "urgency_acc%": urg_rt,
                     "concern%": conc_rt, "latency_ms": avg_lat}

# ── T4 ────────────────────────────────────────────────────────────────────────
if "T4" in all_results:
    rs = all_results["T4"]
    n  = len(rs)
    json_rt  = round(sum(r.get("json_valid", False) for r in rs) / n * 100, 1)
    vet_rt   = round(sum(r.get("vet_needed_ok", False) for r in rs) / n * 100, 1)
    home_rt  = round(sum(r.get("home_care_ok", False) for r in rs) / n * 100, 1)
    care_rt  = round(sum(r.get("has_care_steps", False) for r in rs) / n * 100, 1)
    emrg_rt  = round(sum(r.get("has_emerg_signs", False) for r in rs) / n * 100, 1)
    avg_lat  = round(sum(r["latency_ms"] for r in rs) / n)
    print(f"\n💊 T4 — Recommandations ({n} exemples)")
    print(f"   JSON valide      : {json_rt}%")
    print(f"   vet_needed OK    : {vet_rt}%")
    print(f"   home_care_ok OK  : {home_rt}%")
    print(f"   Étapes de soins  : {care_rt}%")
    print(f"   Signes urgence   : {emrg_rt}%")
    print(f"   Latence moy      : {avg_lat}ms")
    summary["T4"] = {"json_valid%": json_rt, "vet_needed_acc%": vet_rt,
                     "home_care_acc%": home_rt, "latency_ms": avg_lat}

# ── T5 ────────────────────────────────────────────────────────────────────────
if "T5" in all_results:
    rs = all_results["T5"]
    n  = len(rs)
    json_rt  = round(sum(r.get("json_valid", False) for r in rs) / n * 100, 1)
    val_rt   = round(sum(r.get("valid_ok", False) for r in rs) / n * 100, 1)
    urg_rt   = round(sum(r.get("urgency_ok", False) for r in rs) / n * 100, 1)
    rea_rt   = round(sum(r.get("has_reason", False) for r in rs) / n * 100, 1)
    conf_rt  = round(sum(r.get("confidence_ok", False) for r in rs) / n * 100, 1)
    avg_lat  = round(sum(r["latency_ms"] for r in rs) / n)
    print(f"\n✔️  T5 — Validation médicale ({n} exemples)")
    print(f"   JSON valide      : {json_rt}%")
    print(f"   valid/invalid OK : {val_rt}%")
    print(f"   Urgence corrigée : {urg_rt}%")
    print(f"   Raison présente  : {rea_rt}%")
    print(f"   Confidence OK    : {conf_rt}%")
    print(f"   Latence moy      : {avg_lat}ms")
    summary["T5"] = {"json_valid%": json_rt, "valid_detection%": val_rt,
                     "urgency_corr%": urg_rt, "latency_ms": avg_lat}

# ── Score global ──────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SCORE GLOBAL")
print("=" * 60)

global_json = round(sum(
    summary.get(t, {}).get("json_valid%", summary.get(t, {}).get("rouge1", 0) * 100)
    for t in ["T2", "T3", "T4", "T5"]
) / 4, 1)

global_urgency = round(sum(
    summary.get(t, {}).get("urgency_acc%", summary.get(t, {}).get("urgency_corr%", 0))
    for t in ["T1", "T2", "T3", "T5"]
) / 4, 1)

avg_latency = round(sum(all_latencies) / len(all_latencies)) if all_latencies else 0

print(f"\n   JSON validity (T2-T5)       : {global_json}%")
print(f"   Urgency accuracy (T1-T5)    : {global_urgency}%")
print(f"   ROUGE-L (T1)                : {summary.get('T1', {}).get('rougeL', 0):.4f}")
print(f"   Disclaimer rate (T1)        : {summary.get('T1', {}).get('disclaimer%', 0)}%")
print(f"   Latence moyenne globale     : {avg_latency}ms")

# ── Sauvegarde du rapport ─────────────────────────────────────────────────────
report = {
    "model"          : "cheebo-multitask (LLaMA 3.1 8B Instruct + LoRA)",
    "n_samples"      : total_samples,
    "n_per_task"     : N_PER_TASK,
    "global_metrics" : {
        "json_validity_%"   : global_json,
        "urgency_accuracy_%": global_urgency,
        "rougeL_T1"         : summary.get("T1", {}).get("rougeL", 0),
        "disclaimer_%"      : summary.get("T1", {}).get("disclaimer%", 0),
        "avg_latency_ms"    : avg_latency,
    },
    "per_task": summary,
}

with open("cheebo_benchmark_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f"\n✅ Rapport sauvegardé → cheebo_benchmark_report.json")
print("=" * 60)
