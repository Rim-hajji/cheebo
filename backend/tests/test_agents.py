"""
DoctoAgent — Script de test des agents
========================================
3 niveaux de test :
  1. Test agent individuel  — un seul agent avec un contexte minimal
  2. Test pipeline complet  — orchestrateur → 8 agents → réponse finale
  3. Test API HTTP          — serveur FastAPI + requête POST

Usage :
  python -m backend.tests.test_agents 1   # test agent individuel
  python -m backend.tests.test_agents 2   # test pipeline complet
  python -m backend.tests.test_agents 3   # test API (serveur doit être lancé)

Auteur : Rim Hajji — PFE 2026
"""

import json
import sys
import textwrap
import time

# Force UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────────────────────────────────────────────────────
# DONNÉES DE TEST
# ──────────────────────────────────────────────────────────────────

# Scénarios NLP simulés (sans passer par le vrai pipeline NLP)
TEST_CASES = [
    {
        "name"        : "Chien — vomissement sang (HIGH)",
        "nlp_dict"    : {
            "original_text"       : "Mon chien vomit du sang depuis ce matin, il est très fatigué",
            "language"            : "fr",
            "intent"              : "describe_symptom",
            "intent_confidence"   : 0.93,
            "urgency_label"       : "HIGH",
            "urgency_score"       : 8,
            "urgency_confidence"  : 0.87,
            "entities"            : [
                {"text": "chien",   "label": "ANIMAL"},
                {"text": "vomit",   "label": "SYMPTOM"},
                {"text": "sang",    "label": "SYMPTOM"},
                {"text": "fatigué", "label": "SYMPTOM"},
                {"text": "ce matin","label": "DUREE"},
            ],
            "ner_source": "vetbert",
        },
    },
    {
        "name"        : "Chat — ne mange plus (MODERATE)",
        "nlp_dict"    : {
            "original_text"       : "Mon chat ne mange plus depuis 2 jours, il dort beaucoup",
            "language"            : "fr",
            "intent"              : "describe_symptom",
            "intent_confidence"   : 0.88,
            "urgency_label"       : "MODERATE",
            "urgency_score"       : 5,
            "urgency_confidence"  : 0.75,
            "entities"            : [
                {"text": "chat",          "label": "ANIMAL"},
                {"text": "ne mange plus", "label": "SYMPTOM"},
                {"text": "dort beaucoup", "label": "SYMPTOM"},
                {"text": "2 jours",       "label": "DUREE"},
            ],
            "ner_source": "vetbert",
        },
    },
    {
        "name"        : "Chien — convulsion urgence (CRITICAL)",
        "nlp_dict"    : {
            "original_text"       : "mon chien fait des convulsions il est inconscient aidez moi",
            "language"            : "fr",
            "intent"              : "emergency",
            "intent_confidence"   : 0.97,
            "urgency_label"       : "CRITICAL",
            "urgency_score"       : 10,
            "urgency_confidence"  : 0.95,
            "entities"            : [
                {"text": "chien",       "label": "ANIMAL"},
                {"text": "convulsions", "label": "SYMPTOM"},
                {"text": "inconscient", "label": "SYMPTOM"},
            ],
            "ner_source": "vetbert",
        },
    },
    {
        "name"        : "Chien — toux légère (LOW)",
        "nlp_dict"    : {
            "original_text"       : "Mon chien tousse un peu depuis hier soir",
            "language"            : "fr",
            "intent"              : "describe_symptom",
            "intent_confidence"   : 0.82,
            "urgency_label"       : "LOW",
            "urgency_score"       : 2,
            "urgency_confidence"  : 0.78,
            "entities"            : [
                {"text": "chien",      "label": "ANIMAL"},
                {"text": "tousse",     "label": "SYMPTOM"},
                {"text": "hier soir",  "label": "DUREE"},
            ],
            "ner_source": "vetbert",
        },
    },
]


# ──────────────────────────────────────────────────────────────────
# HELPERS D'AFFICHAGE
# ──────────────────────────────────────────────────────────────────

def _sep(title: str = ""):
    width = 65
    if title:
        print(f"\n--- {title} {'-' * max(0, width - len(title) - 5)}")
    else:
        print("-" * width)


def _wrap(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    return textwrap.fill(str(text), width=72, initial_indent=prefix,
                         subsequent_indent=prefix)


def _print_response(response: dict):
    """Affiche les sections clés de la réponse finale."""
    status = response.get("status", "?")
    print(f"  status        : {status}")

    if status == "error":
        print(f"  error         : {response.get('error')}")
        return

    # Urgence
    urgency = response.get("urgency", {})
    print(f"  urgence       : {urgency.get('level')} "
          f"(score {urgency.get('score')}/10) — {urgency.get('label', '')}")
    if urgency.get("red_flags_found"):
        print(f"  red flags     : {urgency['red_flags_found']}")
    if urgency.get("was_escalated"):
        print(f"  escaladé      : Oui — {urgency.get('escalation_triggers', [])}")

    # Urgence médicale
    emergency = response.get("emergency", {})
    print(f"  urgence méd.  : {'OUI 🚨' if emergency.get('is_emergency') else 'Non'}")
    if emergency.get("alert_message"):
        print(_wrap(f"alerte : {emergency['alert_message']}"))

    # Symptômes
    symptoms = response.get("symptoms", {})
    print(f"  animal        : {symptoms.get('animal', '?')}")
    print(f"  symptômes KB  : {symptoms.get('symptoms_normalized', [])}")

    # Pistes d'orientation
    preds = response.get("predictions", {})
    assoc = preds.get("possible_associations", [])
    if assoc:
        print(f"  pistes ({len(assoc)})    :")
        for a in assoc[:3]:
            print(f"    • {a.get('condition')} [{a.get('frequency')}]"
                  f" — vet={a.get('requires_vet')}")
    if preds.get("orientation_summary"):
        print(_wrap(f"orientation : {preds['orientation_summary']}"))

    # Plan de soin
    care = response.get("care_plan", {})
    if care.get("immediate_actions"):
        print(f"  actions imm.  : {care['immediate_actions'][:2]}")
    if care.get("home_care_steps"):
        print(f"  soins maison  : {care['home_care_steps'][:2]}")
    if care.get("when_to_consult"):
        print(_wrap(f"quand consult : {care['when_to_consult']}"))

    # Message principal
    main_msg = response.get("main_message", "")
    if main_msg:
        print(_wrap(f"message : {main_msg}"))

    # Timings
    meta = response.get("metadata", {})
    print(f"  agents        : {meta.get('agents_used', [])}")
    print(f"  durée totale  : {meta.get('total_processing_ms', 0):.0f} ms")


# ──────────────────────────────────────────────────────────────────
# NIVEAU 1 — TEST AGENT INDIVIDUEL
# ──────────────────────────────────────────────────────────────────

def test_single_agent():
    """Teste un seul agent avec un contexte minimal."""
    import os
    sys.path.insert(0, ".")
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    from backend.agents.tools import init_kb
    from backend.agents.symptom_agent import SymptomAgent

    print("\n" + "=" * 65)
    print("TEST NIVEAU 1 — Agent individuel : SymptomAgent")
    print("=" * 65)

    # Charger la KB
    with open("backend/data/symptom_kb.json", encoding="utf-8") as f:
        kb = json.load(f)
    init_kb(kb)
    print(f"  KB chargée : {len(kb)} symptômes\n")

    agent = SymptomAgent()

    for case in TEST_CASES[:2]:
        _sep(case["name"])
        t0 = time.perf_counter()
        result = agent.run(case["nlp_dict"])
        ms = (time.perf_counter() - t0) * 1000

        print(f"  animal      : {result.get('animal')}")
        print(f"  symptômes   : {result.get('symptoms_raw')}")
        print(f"  normalisés  : {result.get('symptoms_normalized')}")
        print(f"  sévérité    : {result.get('severity_indicators')}")
        print(f"  flag        : {result.get('has_severity_flag')}")
        print(f"  confiance   : {result.get('confidence')}")
        print(f"  durée agent : {ms:.0f} ms")
        if result.get("status") == "fallback":
            print(f"  ⚠️ FALLBACK : {result.get('reasoning')}")


# ──────────────────────────────────────────────────────────────────
# NIVEAU 2 — TEST PIPELINE COMPLET
# ──────────────────────────────────────────────────────────────────

def test_full_pipeline(case_index: int = 0):
    """Teste le pipeline complet via l'orchestrateur."""
    import os
    sys.path.insert(0, ".")
    os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    with open("backend/data/symptom_kb.json", encoding="utf-8") as f:
        kb = json.load(f)

    from backend.agents.orchestrator import Orchestrator

    print("\n" + "=" * 65)
    print("TEST NIVEAU 2 — Pipeline complet (LangGraph + 8 agents)")
    print("=" * 65)

    orch = Orchestrator(kb_data=kb)
    print("  Orchestrateur initialisé\n")

    case = TEST_CASES[case_index]
    _sep(f"Scénario : {case['name']}")
    print(f"  Texte : \"{case['nlp_dict']['original_text']}\"")
    print(f"  NLP urgence : {case['nlp_dict']['urgency_label']}\n")

    t0 = time.perf_counter()
    response = orch.handle(case["nlp_dict"])
    total_ms = (time.perf_counter() - t0) * 1000

    print(f"\n{'=' * 65}")
    print(f"  REPONSE FINALE ({total_ms:.0f} ms total)")
    print(f"{'=' * 65}")
    _print_response(response)


# ──────────────────────────────────────────────────────────────────
# NIVEAU 3 — TEST API HTTP
# ──────────────────────────────────────────────────────────────────

def test_api(base_url: str = "http://localhost:8000"):
    """Teste l'API FastAPI via des requêtes HTTP."""
    import urllib.request

    print("\n" + "=" * 65)
    print(f"TEST NIVEAU 3 — API HTTP ({base_url})")
    print("=" * 65)

    # Health check
    try:
        with urllib.request.urlopen(f"{base_url}/", timeout=3) as r:
            health = json.loads(r.read())
        print(f"  ✅ Serveur actif : {health.get('message')}\n")
    except Exception as e:
        print(f"  ❌ Serveur inaccessible : {e}")
        print(f"     Lance le serveur avec : uvicorn backend.api.main:app --reload")
        return

    # Test /analyze
    for case in TEST_CASES[:2]:
        _sep(case["name"])
        payload = json.dumps({"text": case["nlp_dict"]["original_text"]}).encode()
        req = urllib.request.Request(
            f"{base_url}/api/v1/analyze",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            t0 = time.perf_counter()
            with urllib.request.urlopen(req, timeout=120) as r:
                response = json.loads(r.read())
            ms = (time.perf_counter() - t0) * 1000
            print(f"  HTTP 200 OK ({ms:.0f} ms)")
            _print_response(response)
        except Exception as e:
            print(f"  ❌ Erreur : {e}")


# ──────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    case  = int(sys.argv[2]) if len(sys.argv) > 2 else 0

    if level == 1:
        test_single_agent()
    elif level == 2:
        test_full_pipeline(case_index=case)
    elif level == 3:
        test_api()
    else:
        print("Usage : python -m backend.tests.test_agents [1|2|3] [case_index]")
        print("  1 = agent individuel (SymptomAgent)")
        print("  2 = pipeline complet (défaut)")
        print("  3 = API HTTP (serveur doit être lancé)")
        print()
        print("Scénarios disponibles :")
        for i, c in enumerate(TEST_CASES):
            print(f"  {i} — {c['name']}")
