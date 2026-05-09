"""
DoctoAgent — Route /chat
=========================
Endpoint conversationnel : gère le contexte de session, pose des questions
de suivi si nécessaire, puis déclenche le pipeline multi-agents pour produire
une réponse adaptée au niveau d'urgence.

Le pipeline retourne une réponse structurée (urgency, care_plan, emergency,
predictions, rag_advice, recommendation…). Ce module la transforme en message
conversationnel lisible pour l'application Flutter.

Auteur : Rim Hajji — PFE 2026
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from backend.agents.shared import orchestrator
from backend.agents.tools import PARTNER_VETS
from backend.database.mongo import conversations as conv_col, analysis_logs as logs_col
from backend.nlp.pipeline import nlp_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Persistence MongoDB (background, non bloquant) ───────────────────

async def _save_to_mongo(
    session_id   : str,
    user_msg     : str,
    agent_content: str,
    agent_type   : str,
    urgency_label: Optional[str],
    partner_vets : Optional[list],
    nlp_dict     : dict,
    final_resp   : dict,
):
    """Sauvegarde la conversation et le log d'analyse dans MongoDB."""
    try:
        now = datetime.now(timezone.utc)

        # ── Conversation (upsert) ─────────────────────────────
        user_message_doc = {
            "role"     : "user",
            "content"  : user_msg,
            "timestamp": now,
        }
        agent_message_doc = {
            "role"         : "agent",
            "content"      : agent_content,
            "agent_type"   : agent_type,
            "urgency_label": urgency_label,
            "partner_vets" : partner_vets,
            "timestamp"    : now,
        }
        title = user_msg[:60] + ("…" if len(user_msg) > 60 else "")
        await conv_col().update_one(
            {"session_id": session_id},
            {
                "$setOnInsert": {
                    "session_id": session_id,
                    "title"     : title,
                    "language"  : nlp_dict.get("language", "fr"),
                    "created_at": now,
                },
                "$set"      : {"updated_at": now},
                "$push"     : {"messages": {"$each": [user_message_doc, agent_message_doc]}},
                "$inc"      : {"message_count": 2},
            },
            upsert=True,
        )

        # ── Log d'analyse ──────────────────────────────────────
        meta = final_resp.get("metadata", {})
        await logs_col().insert_one({
            "session_id"    : session_id,
            "original_text" : nlp_dict.get("original_text", user_msg),
            "language"      : nlp_dict.get("language", "fr"),
            "intent"        : nlp_dict.get("intent", ""),
            "urgency_level" : urgency_label,
            "urgency_score" : final_resp.get("urgency", {}).get("score"),
            "entities"      : nlp_dict.get("entities", []),
            "agents_used"   : meta.get("agents_used", []),
            "processing_ms" : meta.get("total_processing_ms"),
            "created_at"    : now,
        })

    except Exception as e:
        logger.warning(f"[Chat] Sauvegarde MongoDB échouée : {e}")

# ── Réponses contextuelles sans LLM ──────────────────────────────
_NO_SYMPTOM_REPLIES = {
    "fr": {
        "with_animal": [
            "Je vois que vous parlez de votre {animal} 🐾 Que se passe-t-il exactement ? Décrivez-moi ce que vous observez.",
            "Votre {animal} vous inquiète ? Dites-moi quels symptômes vous avez remarqués.",
            "Pour aider votre {animal}, j'ai besoin d'en savoir plus. Quels signes inhabituels avez-vous observés ?",
        ],
        "no_animal": [
            "Je suis Cheebo, votre assistant vétérinaire 🐾 Décrivez-moi les symptômes de votre animal.",
            "Pour vous guider au mieux, pouvez-vous me décrire ce qui préoccupe votre compagnon ?",
            "Quel problème observez-vous chez votre animal ? Je suis là pour vous aider.",
        ],
    },
    "en": {
        "with_animal": [
            "I see you're talking about your {animal} 🐾 What's going on exactly? Describe what you're observing.",
            "Is your {animal} worrying you? Tell me what symptoms you've noticed.",
            "To help your {animal}, I need more details. What unusual signs have you noticed?",
        ],
        "no_animal": [
            "I'm Cheebo, your veterinary assistant 🐾 Please describe your pet's symptoms.",
            "To guide you best, can you describe what's worrying you about your companion?",
            "What issue are you observing in your pet? I'm here to help.",
        ],
    },
    "ar": {
        "with_animal": [
            "أرى أنك تتحدث عن {animal} 🐾 ما الذي يحدث بالضبط؟ صف لي ما تلاحظه.",
            "هل {animal} يقلقك؟ أخبرني بالأعراض التي لاحظتها.",
            "لمساعدة {animal}، أحتاج إلى مزيد من التفاصيل. ما العلامات غير المعتادة التي لاحظتها؟",
        ],
        "no_animal": [
            "أنا Cheebo، مساعدك البيطري 🐾 صف لي أعراض حيوانك الأليف.",
            "لإرشادك بشكل أفضل، هل يمكنك وصف ما يقلقك في حيوانك؟",
            "ما المشكلة التي تلاحظها في حيوانك الأليف؟ أنا هنا للمساعدة.",
        ],
    },
}


# Mots-clés symptômes FR + EN — filet de sécurité si NER rate
_SYMPTOM_KW = [
    # Français
    "vomit", "vomiss", "diarrhé", "mange pas", "n'mange", "ne mange",
    "perd l'appétit", "perte d'appétit", "boite", "boiterie", "tousse",
    "toux", "fatigu", "léthargi", "apathi", "somnolent", "dort beaucoup",
    "maigr", "urine", "boit beaucoup", "se gratte", "gratte", "plaie",
    "blessure", "saigne", "sang", "convuls", "tremble", "gonfl",
    "abcès", "pus", "larmoie", "coule", "écoulement", "respir",
    "avale", "yeux", "oreill", "pelage", "poil", "léthargique",
    "paresseux", "abattu", "prostr", "ne boit", "ne joue", "ne bouge",
    "manguent pas", "perd du poids", "perd poids", "mince", "malade",
    "douleur", "souffre", "gémit", "gémiss", "pleure", "moucheux",
    "démangeaison", "peau", "liquide", "écoulement", "nez",
    "ne mange plus", "mange moins", "dort plus", "moins actif",
    "pas d'énergie", "yeux larmoyants", "yeux qui coulent",
    # English
    "vomit", "diarrhea", "not eating", "won't eat", "doesn't eat",
    "limp", "cough", "letharg", "fatigue", "sleepy", "losing weight",
    "scratching", "wound", "bleed", "blood", "seizure", "trembl",
    "swelling", "abscess", "discharge", "not breathing", "swallow",
    "not moving", "weak", "loss of appetite", "not drink", "pale gums",
    "watery eye", "runny nose", "sneezing", "wheezing", "itching",
    "scratching", "limping", "shaking", "drooling", "panting",
]


def _has_symptom_keywords(text: str) -> bool:
    """Détecte les symptômes par mots-clés quand le NER échoue (FR/EN/AR)."""
    t = text.lower()
    return any(kw in t for kw in _SYMPTOM_KW)


def _no_symptom_reply(language: str, entities: list) -> str:
    """Réponse contextuelle basée sur le NLP — aucun appel LLM."""
    lang = language if language in _NO_SYMPTOM_REPLIES else "fr"
    pool = _NO_SYMPTOM_REPLIES[lang]

    animals = [e["text"] for e in entities if e.get("label") == "ANIMAL"]
    if animals:
        animal = animals[0]
        template = random.choice(pool["with_animal"])
        return template.format(animal=animal)
    return random.choice(pool["no_animal"])


# ──────────────────────────────────────────────────────────────────
# SCHÉMAS
# ──────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str            # "user" | "agent"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    session_id: str
    response: str
    agent_type: str      # "GREETING" | "QUESTION" | "ANALYSIS" | "EMERGENCY"
    urgency_label: Optional[str] = None
    full_data: Optional[Dict] = None
    partner_vets: Optional[List] = None


# ──────────────────────────────────────────────────────────────────
# TEXTES FIXES
# ──────────────────────────────────────────────────────────────────

GREETING = (
    "🐾 Bonjour ! Je suis **Cheebo**, votre assistant santé vétérinaire.\n\n"
    "Je suis là pour analyser les symptômes de votre animal et vous guider "
    "vers les bons soins préventifs.\n\n"
    "Dites-moi : **comment va votre compagnon aujourd'hui ?** 🐶🐱"
)

FOLLOW_UP_QUESTIONS = {
    "duree"       : "⏱️ Depuis combien de temps observez-vous ces symptômes ?",
    "repas"       : "🍽️ Votre animal mange-t-il normalement ?",
    "hydratation" : "💧 Boit-il suffisamment ? Semble-t-il déshydraté ?",
    "comportement": "🎾 Son comportement est-il normal ? Est-il actif ?",
}


def _get_partner_vets(level: str) -> Optional[List[Dict]]:
    """Retourne les vétérinaires partenaires selon le niveau d'urgence."""
    if level == "LOW":
        return None
    if level in ("HIGH", "CRITICAL"):
        return [v for v in PARTNER_VETS if v["available"] and v["emergency"]]
    # MODERATE : tous les vets disponibles
    return [v for v in PARTNER_VETS if v["available"]]


# Mots-clés indiquant que l'info est déjà dans le message utilisateur
_INFO_PRESENT_KW = {
    "duree": [
        "depuis", "il y a", "ça fait", "cela fait", "since", "for ", "ago",
        "hier", "matin", "soir", "nuit", "yesterday", "morning",
        "jour", "jours", "heure", "heures", "semaine", "mois",
        "day", "days", "hour", "hours", "week", "month",
        "2 ", "3 ", "4 ", "5 ", "6 ", "7 ",
    ],
    "repas": [
        "mange", "manger", "appétit", "nourriture", "repas", "croquette",
        "mange pas", "ne mange", "mange moins", "mange plus", "refuse",
        "eat", "eating", "food", "appetite", "hungry", "not eating",
    ],
    "comportement": [
        "létharg", "apathi", "actif", "joue", "énergie", "dort", "fatigue",
        "abattu", "prostr", "normal", "habituel", "moins actif",
        "letharg", "active", "playing", "energy", "sleeping", "tired",
        "playful", "energetic", "lazy",
    ],
}


def _info_already_in_message(text: str, key: str) -> bool:
    """True si le message contient déjà l'info demandée par la question de suivi."""
    t = text.lower()
    return any(kw in t for kw in _INFO_PRESENT_KW.get(key, []))


def _already_asked(history: List[ChatMessage], key: str) -> bool:
    snippet = FOLLOW_UP_QUESTIONS[key][:25]
    return any(snippet in m.content for m in history if m.role == "agent")


def _last_agent_was_question(history: List[ChatMessage]) -> bool:
    """True si le dernier message agent était une question de suivi."""
    for msg in reversed(history):
        if msg.role == "agent":
            return any(q[:20] in msg.content for q in FOLLOW_UP_QUESTIONS.values())
    return False


def _find_first_user_message(history: List[ChatMessage]) -> Optional[str]:
    """Retourne le premier message utilisateur (la description originale des symptômes)."""
    for msg in history:
        if msg.role == "user":
            return msg.content
    return None


# ──────────────────────────────────────────────────────────────────
# CONSTRUCTION DU MESSAGE CONVERSATIONNEL
# ──────────────────────────────────────────────────────────────────

def _build_chat_response(data: Dict) -> str:
    """Construit un message conversationnel adapté au cas spécifique."""
    level     = data.get("urgency", {}).get("level", "LOW")
    emergency = data.get("emergency", {})
    care      = data.get("care_plan", {})
    preds     = data.get("predictions", {})
    rec       = data.get("recommendation", {})
    symptoms  = data.get("symptoms", {})

    headers = {
        "CRITICAL": "🚨 **URGENCE CRITIQUE**",
        "HIGH"    : "⚠️ **Situation préoccupante**",
        "MODERATE": "📋 **Surveillance recommandée**",
        "LOW"     : "✅ **Situation bénigne**",
    }
    lines = [headers.get(level, "📋 **Analyse**"), ""]

    # ── Message principal contextuel (vient de Gemini via RecommendationAgent) ──
    main_msg = data.get("main_message") or rec.get("message", "")
    if main_msg:
        lines += [main_msg, ""]

    # ── CRITIQUE / HIGH : urgence immédiate ──────────────────────────
    if level in ("CRITICAL", "HIGH"):
        alert = emergency.get("alert_message", "")
        if alert and alert != main_msg:
            lines += [f"**🚑 {alert}**", ""]

        actions = (emergency.get("immediate_actions") or
                   care.get("immediate_actions", []))
        if actions:
            lines.append("**⚡ À faire maintenant :**")
            for a in actions[:4]:
                lines.append(f"• {a}")
            lines.append("")

        vets = emergency.get("partner_vets", [])
        if vets:
            lines.append("**🏥 Vétérinaires disponibles :**")
            for v in vets[:2]:
                lines.append(f"• **{v.get('name')}** — {v.get('phone', '')}")
            lines.append("")

    # ── LOW / MODERATE : prédictions + soins ─────────────────────────
    else:
        # ── Pistes possibles (PredictionAgent via KB) ────────────────
        associations = preds.get("possible_associations", [])
        main_concern = preds.get("main_concern", "")
        orientation  = preds.get("orientation_summary", "")

        if associations:
            lines.append("**🔍 Ce que ces symptômes peuvent indiquer :**")
            for assoc in associations[:3]:
                condition = assoc.get("condition", "")
                freq      = assoc.get("frequency", "")
                srcs      = assoc.get("source_symptoms", [])
                watch     = assoc.get("watch_for", "")
                freq_label = {"HIGH": "fréquent", "MEDIUM": "possible", "LOW": "rare"}.get(freq, "possible")
                src_str = ", ".join(srcs[:2]) if srcs else ""
                cond_line = f"• **{condition}** ({freq_label})"
                if src_str:
                    cond_line += f" — lié à : {src_str}"
                lines.append(cond_line)
                if watch:
                    lines.append(f"  _⚠️ Consultez si : {watch}_")
            lines.append("")
        elif main_concern and main_concern not in ("Symptômes à surveiller", ""):
            lines += [f"🔍 **Point de vigilance** : {main_concern}", ""]
        elif orientation and orientation not in ("Surveillance recommandée. Consultez un vétérinaire si les symptômes persistent.", ""):
            lines += [f"🔍 {orientation}", ""]

        # ── Plan de soin (CareAgent via KB) ─────────────────────────
        care_summary = care.get("care_summary", "")
        if care_summary and care_summary not in ("Plan de soin par défaut — conseils généraux.", ""):
            lines += [f"💬 {care_summary}", ""]

        home_care = care.get("home_care_steps", [])
        if home_care:
            lines.append("**💊 À faire à la maison :**")
            for c in home_care[:4]:
                lines.append(f"• {c}")
            lines.append("")

        diet = care.get("diet_advice")
        if diet:
            lines += [f"🍽️ {diet}", ""]

        if level == "MODERATE":
            imm = care.get("immediate_actions", [])
            if imm:
                lines.append("**⚡ Actions prioritaires :**")
                for a in imm[:2]:
                    lines.append(f"• {a}")
                lines.append("")

        when = care.get("when_to_consult", "")
        if when:
            lines += [f"📅 **Quand consulter** : {when}", ""]

    # ── Signes d'alarme ──────────────────────────────────────────────
    monitoring = care.get("monitoring_signs", [])
    if monitoring:
        if len(monitoring) == 1:
            lines += [f"👁️ **À surveiller** : {monitoring[0]}", ""]
        else:
            lines.append("👁️ **Signes d'alarme à surveiller :**")
            for s in monitoring[:3]:
                lines.append(f"• {s}")
            lines.append("")

    # ── Évolution attendue ───────────────────────────────────────────
    timeline = care.get("timeline", [])
    if timeline and level in ("MODERATE", "HIGH"):
        first = timeline[0]
        tf   = first.get("timeframe", "")
        desc = first.get("description", "")
        if tf and desc:
            lines += [f"⏱️ **Dans {tf}** : {desc}", ""]

    lines.append("_Ces conseils ne remplacent pas l'avis d'un vétérinaire._")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────
# ROUTE PRINCIPALE
# ──────────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """Endpoint conversationnel principal de DoctoAgent / Cheebo."""
    session_id   = request.session_id or str(uuid.uuid4())
    history      = request.history
    user_message = request.message.strip()

    logger.info(f"[Chat {session_id[:8]}] User: '{user_message[:60]}'")

    # Cas 1 : Premier message → salutation
    if not history:
        return ChatResponse(
            session_id=session_id,
            response=GREETING,
            agent_type="GREETING",
        )

    try:
        # Si l'utilisateur répond à une question de suivi, combiner avec le message original
        # pour ne pas perdre le contexte des symptômes initiaux
        if _last_agent_was_question(history):
            original = _find_first_user_message(history)
            if original and original.lower() != user_message.lower():
                analysis_text = f"{original}. {user_message}"
            else:
                analysis_text = user_message
        else:
            analysis_text = user_message

        # Analyse NLP + pipeline multi-agents
        nlp_result = nlp_pipeline.process(analysis_text)

        # Extraire les entités NLP
        nlp_dict = nlp_result if isinstance(nlp_result, dict) else (
            nlp_result.model_dump() if hasattr(nlp_result, "model_dump") else vars(nlp_result)
        )
        entities       = nlp_dict.get("entities", [])
        intent         = nlp_dict.get("intent", "")
        urgency_from_nlp = nlp_dict.get("urgency_label", "LOW")
        has_symptom    = (
            any(e.get("label") == "SYMPTOM" for e in entities)
            or _has_symptom_keywords(analysis_text)
            or urgency_from_nlp in ("MODERATE", "HIGH", "CRITICAL")
        )
        has_animal     = any(e.get("label") == "ANIMAL" for e in entities)
        duree_detected = any(e.get("label") == "DUREE" for e in entities)

        # Cas : pas de symptôme détecté → réponse contextuelle sans LLM
        is_answering_followup = _last_agent_was_question(history)
        if not has_symptom and intent not in ("emergency",) and not is_answering_followup:
            language = nlp_dict.get("language", "fr")
            reply = _no_symptom_reply(language, entities)
            return ChatResponse(
                session_id = session_id,
                response   = reply,
                agent_type = "QUESTION",
            )

        loop = asyncio.get_event_loop()
        final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)

        # Niveau d'urgence depuis la réponse du pipeline (post-raffinement LLM)
        level = final_response.get("urgency", {}).get("level", "LOW")

        vets = _get_partner_vets(level)

        def _get_response_text(data: dict) -> str:
            """Utilise la réponse du SynthesisAgent (Gemini) ; fallback sur templates."""
            synthesis = data.get("synthesis", {})
            text = synthesis.get("response_text", "")
            if text and len(text.strip()) > 20:
                return text.strip()
            return _build_chat_response(data)

        # Cas 2 : Urgence HIGH/CRITICAL → réponse directe sans questions
        if level in ("CRITICAL", "HIGH"):
            chat_text = _get_response_text(final_response)
            background_tasks.add_task(
                _save_to_mongo,
                session_id, user_message, chat_text, "EMERGENCY",
                level, vets, nlp_dict, final_response,
            )
            return ChatResponse(
                session_id    = session_id,
                response      = chat_text,
                agent_type    = "EMERGENCY",
                urgency_label = level,
                full_data     = final_response,
                partner_vets  = vets,
            )

        # Cas 3 : MODERATE → poser 1 question de suivi si info manquante
        if level == "MODERATE":
            for key in ("duree", "repas", "comportement"):
                if key == "duree" and duree_detected:
                    continue
                if _info_already_in_message(analysis_text, key):
                    continue
                if not _already_asked(history, key):
                    prefix = (
                        "Je comprends, votre animal ne va pas très bien. "
                        "Pour mieux évaluer la situation, j'aurais besoin d'une précision :\n\n"
                    )
                    return ChatResponse(
                        session_id    = session_id,
                        response      = prefix + FOLLOW_UP_QUESTIONS[key],
                        agent_type    = "QUESTION",
                        urgency_label = level,
                    )
            chat_text = _get_response_text(final_response)
            background_tasks.add_task(
                _save_to_mongo,
                session_id, user_message, chat_text, "ANALYSIS",
                level, vets, nlp_dict, final_response,
            )
            return ChatResponse(
                session_id    = session_id,
                response      = chat_text,
                agent_type    = "ANALYSIS",
                urgency_label = level,
                full_data     = final_response,
                partner_vets  = vets,
            )

        # Cas 4 : LOW → analyse directe (pas de vets)
        chat_text = _get_response_text(final_response)
        background_tasks.add_task(
            _save_to_mongo,
            session_id, user_message, chat_text, "ANALYSIS",
            level, None, nlp_dict, final_response,
        )
        return ChatResponse(
            session_id    = session_id,
            response      = chat_text,
            agent_type    = "ANALYSIS",
            urgency_label = level,
            full_data     = final_response,
        )

    except Exception as e:
        logger.error(f"[Chat {session_id[:8]}] Erreur : {e}", exc_info=True)
        return ChatResponse(
            session_id = session_id,
            response   = (
                "😔 Désolé, j'ai rencontré un problème technique. "
                "Pouvez-vous reformuler votre message ?"
            ),
            agent_type = "ERROR",
        )
