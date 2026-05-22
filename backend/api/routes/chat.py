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

import base64
import json as json_lib

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from backend.agents.shared import orchestrator
from backend.agents.tools import PARTNER_VETS
from backend.agents.groq_guard import groq_guard
from backend.database.mongo import conversations as conv_col, analysis_logs as logs_col
from backend.nlp.pipeline import nlp_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Persistence MongoDB (background, non bloquant) ───────────────────

def _sanitize(obj):
    """Convertit les types non-BSON-sérialisables en types Python natifs."""
    import numpy as np
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


async def _save_to_mongo(
    session_id   : str,
    user_msg     : str,
    agent_content: str,
    agent_type   : str,
    urgency_label: Optional[str],
    partner_vets : Optional[list],
    nlp_dict     : dict,
    final_resp   : dict,
    images_base64: Optional[List[str]] = None,
):
    """Sauvegarde la conversation et le log d'analyse dans MongoDB."""
    now = datetime.now(timezone.utc)

    # ── Conversation (upsert) ─────────────────────────────────
    try:
        user_message_doc = {
            "role"         : "user",
            "content"      : user_msg,
            "timestamp"    : now,
            **({"images_base64": images_base64} if images_base64 else {}),
        }
        agent_message_doc = {
            "role"         : "agent",
            "content"      : agent_content,
            "agent_type"   : agent_type,
            "urgency_label": urgency_label,
            "partner_vets" : _sanitize(partner_vets) if partner_vets else None,
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
                "$set"  : {"updated_at": now},
                "$push" : {"messages": {"$each": [user_message_doc, agent_message_doc]}},
                "$inc"  : {"message_count": 2},
            },
            upsert=True,
        )
        logger.info(f"[Chat] Conversation {session_id[:8]} sauvegardée dans MongoDB")
    except Exception as e:
        logger.error(f"[Chat] Échec sauvegarde conversation {session_id[:8]} : {e}", exc_info=True)

    # ── Log d'analyse ─────────────────────────────────────────
    try:
        meta = final_resp.get("metadata", {})
        await logs_col().insert_one({
            "session_id"    : session_id,
            "original_text" : user_msg,
            "language"      : nlp_dict.get("language", "fr"),
            "intent"        : nlp_dict.get("intent", ""),
            "urgency_level" : urgency_label,
            "urgency_score" : nlp_dict.get("urgency_score"),
            "entities"      : _sanitize(nlp_dict.get("entities", [])),
            "agents_used"   : meta.get("agents_used", []),
            "processing_ms" : meta.get("total_processing_ms"),
            "created_at"    : now,
        })
    except Exception as e:
        logger.error(f"[Chat] Échec log analyse {session_id[:8]} : {e}", exc_info=True)

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
    "symptôme", "symptomes", "symptômes", "persist", "toujours",
    "encore", "continue", "aggrav", "empire", "s'améliore pas",
    "ne s'améliore", "toujours pareil", "même état",
    # English
    "vomit", "diarrhea", "not eating", "won't eat", "doesn't eat",
    "limp", "cough", "letharg", "fatigue", "sleepy", "losing weight",
    "scratching", "wound", "bleed", "blood", "seizure", "trembl",
    "swelling", "abscess", "discharge", "not breathing", "swallow",
    "not moving", "weak", "loss of appetite", "not drink", "pale gums",
    "watery eye", "runny nose", "sneezing", "wheezing", "itching",
    "scratching", "limping", "shaking", "drooling", "panting",
    "symptom", "symptoms", "persists", "still", "continues",
    "getting worse", "worsening", "no improvement", "same",
    # Arabe — أعراض
    "نزيف", "النزيف", "ينزف", "يتقيأ", "قيء", "إسهال", "اسهال", "دم",
    "جرح", "مجروح", "جريح", "مصاب", "إصابة", "جروح",
    "ألم", "الم", "يتألم", "متألم", "تشنج", "ضعف", "حمى", "سعال", "كحة",
    "لا يأكل", "لا يشرب", "لا يتحرك", "لا يمشي", "لا يلعب",
    "يرتجف", "متعب", "مريض", "يعاني", "يبكي", "يصرخ",
    "ورم", "تورم", "قيح", "إفراز", "صعوبة", "تنفس", "يلهث",
    "فقدان الشهية", "يخدش", "جلد", "شعر", "عيون", "أذن",
    "يسقط", "مشلول", "خدر", "كسر", "احمرار", "التهاب",
    "محتضر", "لا يتنفس", "فاقد الوعي", "مغمى عليه",
]


def _normalize_accents(text: str) -> str:
    """Supprime les accents pour une comparaison tolérante aux fautes de frappe."""
    import unicodedata
    return unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("ascii").lower()

_SYMPTOM_KW_NORM = [_normalize_accents(kw) for kw in _SYMPTOM_KW]

def _has_symptom_keywords(text: str) -> bool:
    """Détecte les symptômes par mots-clés, tolérant aux accents et fautes de frappe."""
    t      = text.lower()
    t_norm = _normalize_accents(text)
    return any(kw in t for kw in _SYMPTOM_KW) or any(kw in t_norm for kw in _SYMPTOM_KW_NORM)


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
    has_images: Optional[bool] = False


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

_FOLLOW_UP_BY_LANG = {
    "animal": {
        "fr": "🐾 De quel animal s'agit-il ? (chien, chat, lapin, oiseau...)",
        "en": "🐾 What type of animal is it? (dog, cat, rabbit, bird...)",
        "ar": "🐾 ما نوع حيوانك الأليف؟ (كلب، قط، أرنب، طائر...)",
    },
    "duree": {
        "fr": "⏱️ Depuis combien de temps observez-vous ces symptômes ?",
        "en": "⏱️ How long have you been observing these symptoms?",
        "ar": "⏱️ منذ متى وأنت تلاحظ هذه الأعراض؟",
    },
    "repas": {
        "fr": "🍽️ Votre animal mange-t-il normalement ?",
        "en": "🍽️ Is your pet eating normally?",
        "ar": "🍽️ هل حيوانك يأكل بشكل طبيعي؟",
    },
    "hydratation": {
        "fr": "💧 Boit-il suffisamment ? Semble-t-il déshydraté ?",
        "en": "💧 Is it drinking enough? Does it seem dehydrated?",
        "ar": "💧 هل يشرب بما فيه الكفاية؟ هل يبدو مجففاً؟",
    },
    "comportement": {
        "fr": "🎾 Son comportement est-il normal ? Est-il actif ?",
        "en": "🎾 Is its behavior normal? Is it active?",
        "ar": "🎾 هل سلوكه طبيعي؟ هل هو نشيط؟",
    },
}

def _follow_up_q(key: str, lang: str) -> str:
    return _FOLLOW_UP_BY_LANG[key].get(lang, _FOLLOW_UP_BY_LANG[key]["fr"])

# Clés pour _already_asked (utilise le texte FR comme référence)
FOLLOW_UP_QUESTIONS = {k: v["fr"] for k, v in _FOLLOW_UP_BY_LANG.items()}


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
    "animal": [
        "chien", "chat", "lapin", "hamster", "perroquet", "cochon", "furet",
        "tortue", "oiseau", "cheval", "chatte", "chienne", "chiot", "chaton",
        "dog", "cat", "rabbit", "parrot", "bird", "horse", "guinea", "turtle",
        "mon chien", "mon chat", "ma chatte", "mon lapin", "ma chienne",
        "le chien", "le chat", "la chatte", "notre chien", "notre chat",
        # Arabe
        "كلب", "قط", "قطة", "أرنب", "طائر", "حصان", "هامستر",
        "كلبي", "قطتي", "حيواني",
    ],
    "duree": [
        "depuis", "il y a", "ça fait", "cela fait", "since", "for ", "ago",
        "hier", "matin", "soir", "nuit", "yesterday", "morning",
        "jour", "jours", "heure", "heures", "semaine", "mois",
        "day", "days", "hour", "hours", "week", "month",
        "2 ", "3 ", "4 ", "5 ", "6 ", "7 ",
        # Arabe
        "منذ", "ساعة", "ساعات", "يوم", "أيام", "أسبوع", "شهر", "البارحة", "الأمس",
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


def _build_accumulated_context(user_message: str, history: List[ChatMessage]) -> str:
    """
    Combine tous les messages utilisateur de la session pour maintenir le contexte médical.

    Exemple :
      msg 1 → "my cat is vomiting for 2 days"
      msg 2 → "the symptoms persist for 4 days"
      → analysis_text = "my cat is vomiting for 2 days. the symptoms persist for 4 days"

    Les messages identiques (casse ignorée) sont dédupliqués.
    La taille est bornée à 800 chars pour ne pas surcharger le NLP.
    Les messages avec images sont exclus du contexte NLP (has_images=True).
    """
    prior = [
        m.content.strip() for m in history
        if m.role == "user"
        and m.content.strip()
        and not m.has_images
    ]
    if not prior:
        return user_message

    all_parts = prior + [user_message]

    # Déduplication (ordre préservé, messages récents conservés en cas de doublon)
    seen: set = set()
    unique: list = []
    for part in all_parts:
        if part.lower() not in seen:
            seen.add(part.lower())
            unique.append(part)

    combined = ". ".join(unique)

    # Sécurité taille : garder les 3 derniers messages + courant si trop long
    if len(combined) > 800:
        recent = prior[-3:] + [user_message]
        seen2: set = set()
        unique2: list = []
        for part in recent:
            if part.lower() not in seen2:
                seen2.add(part.lower())
                unique2.append(part)
        combined = ". ".join(unique2)

    return combined


def _info_already_in_message(text: str, key: str) -> bool:
    """True si le message contient déjà l'info demandée par la question de suivi."""
    t = text.lower()
    return any(kw in t for kw in _INFO_PRESENT_KW.get(key, []))


def _already_asked(history: List[ChatMessage], key: str) -> bool:
    snippet = FOLLOW_UP_QUESTIONS[key][:25]
    return any(snippet in m.content for m in history if m.role == "agent")


def _last_agent_was_question(history: List[ChatMessage]) -> bool:
    """True si le dernier message agent était une question de suivi structurée.
    Ne compte pas le GREETING ni les questions libres de Groq."""
    for msg in reversed(history):
        if msg.role == "agent":
            return any(q[:25] in msg.content for q in FOLLOW_UP_QUESTIONS.values())
    return False


def _find_first_user_message(history: List[ChatMessage]) -> Optional[str]:
    """Retourne le premier message utilisateur texte (sans images)."""
    for msg in history:
        if msg.role == "user" and not msg.has_images:
            return msg.content
    return None


# ── Messages purement sociaux : jamais pipeline, peu importe le contexte ───
# Salutations + remerciements + clôtures → toujours contextual_reply/fallback
_SOCIAL_ONLY_MESSAGES = {
    # Salutations
    "hi", "hello", "hey", "salut", "bonjour", "bonsoir", "coucou",
    "hola", "salam", "yo", "sup", "ola", "hiya",
    "مرحبا", "السلام عليكم", "اهلا", "اهلاً", "مرحباً",
    "good morning", "good evening", "good afternoon", "good night",
    # Remerciements
    "merci", "merci beaucoup", "merci bien", "thank you", "thanks",
    "thx", "thank u", "شكرا", "شكراً", "شكرا جزيلا", "مشكور",
    # Clôtures
    "au revoir", "à bientôt", "bonne journée", "bonne soirée",
    "bye", "goodbye", "take care", "مع السلامة", "وداعا",
    # Acquiescements courts seuls
    "ok", "okay", "d'accord", "ок",
}

# ── Détection des messages d'acquittement (chips de confirmation) ──────────
_ACKNOWLEDGMENT_KW = [
    # Français — contact vétérinaire
    "j'ai contacté", "j'ai appelé", "j'ai appel", "on a appelé",
    "je vais y aller", "on part", "on y va", "je pars",
    "je l'emmène", "je l'amène", "on l'emmène", "on l'amène",
    # Français — amélioration
    "c'est mieux", "il va mieux", "elle va mieux", "ça va mieux",
    "ça s'améliore", "il s'améliore", "elle s'améliore",
    "il récupère", "elle récupère", "il va bien", "elle va bien",
    # English — vet contact
    "i contacted", "i called", "i've called", "we called",
    "we're going", "i'm going", "on our way", "heading to",
    "i took", "we took", "took him", "took her",
    # English — improvement
    "it's better", "he's better", "she's better", "getting better",
    "improving", "recovered", "feeling better", "doing better",
    # Arabe — contact vétérinaire
    "اتصلت", "اتصلنا", "ذهبنا", "سنذهب", "أخذته", "أخذناه",
    # Arabe — amélioration
    "يتحسن", "تحسن", "أفضل", "بخير", "يتعافى", "تعافى",
    # Remerciements / clôture FR
    "merci", "merci beaucoup", "merci bien", "c'est parfait", "parfait merci",
    "ok merci", "d'accord merci", "au revoir", "à bientôt", "bonne journée",
    # Remerciements / clôture EN
    "thank you", "thanks", "thx", "thank u", "many thanks",
    "ok thanks", "ok thank you", "goodbye", "bye", "take care",
    # Remerciements / clôture AR
    "شكرا", "شكراً", "شكرا جزيلا", "مشكور", "مع السلامة", "وداعا",
]

_ACKNOWLEDGMENT_REPLIES = {
    "fr": [
        "Je suis soulagé(e) que vous ayez pris les choses en main 🐾 J'espère que votre compagnon se rétablit vite. N'hésitez pas à me revenir si vous avez d'autres questions !",
        "Parfait, vous faites exactement ce qu'il faut 🌿 J'espère que votre animal se rétablit vite. Je suis là si besoin !",
        "Très bien ! Votre animal a de la chance de vous avoir 🐶 Si les symptômes évoluent, n'hésitez pas à me recontacter.",
    ],
    "en": [
        "Great, I'm glad you're taking action 🐾 I hope your companion recovers quickly! Don't hesitate to reach out if you have more questions.",
        "Perfect, you're doing exactly the right thing 🌿 Wishing your pet a speedy recovery!",
        "Wonderful! Your pet is lucky to have you 🐶 If symptoms change, feel free to reach back out.",
    ],
    "ar": [
        "أنا سعيد أنك اتخذت الإجراء اللازم 🐾 أتمنى لحيوانك الأليف التعافي السريع! لا تتردد في التواصل معي إذا كان لديك المزيد من الأسئلة.",
    ],
}

def _is_acknowledgment(text: str) -> bool:
    """True si le message est un chip d'acquittement (confirmation d'action ou remerciement)."""
    t = text.lower().strip()
    return any(kw in t for kw in _ACKNOWLEDGMENT_KW)


def _acknowledgment_reply(language: str) -> str:
    lang = language if language in _ACKNOWLEDGMENT_REPLIES else "fr"
    return random.choice(_ACKNOWLEDGMENT_REPLIES[lang])


# ──────────────────────────────────────────────────────────────────
# NETTOYAGE DE LA SORTIE DES AGENTS
# ──────────────────────────────────────────────────────────────────

def _clean_agent_text(text: str) -> str:
    """
    Nettoie définitivement la sortie brute de SynthesisAgent avant affichage :
      1. Désenveloppe le JSON si l'agent retourne {"response_text":"..."} malgré la consigne
      2. Supprime les blocs JSON embarqués au milieu du texte
      3. Convertit les \\n littéraux en vrais sauts de ligne
      4. Déduplique les blocs et lignes répétés
      5. Filtre anti-numéros de téléphone (sécurité finale)
    """
    import json as _json
    import re as _re
    from backend.agents.groq_guard import _strip_phones

    if not text:
        return text

    text = text.strip()

    # 1. Si le texte EST entièrement du JSON → extraire la valeur texte
    if text.startswith("{"):
        try:
            obj = _json.loads(text)
            if isinstance(obj, dict):
                for key in ("response_text", "responsetext", "response", "text", "content", "message"):
                    val = obj.get(key) or obj.get(key.upper()) or obj.get(key.title())
                    if isinstance(val, str) and len(val) > 20:
                        text = val
                        break
                else:
                    for val in obj.values():
                        if isinstance(val, str) and len(val) > 20:
                            text = val
                            break
        except Exception:
            # JSON malformé — regex pour extraire la valeur après "response_text":
            m = _re.search(
                r'["\'](?:response_?text|responsetext|response|content)["\']'
                r'\s*:\s*["\'](.{20,}?)(?:["\'](?:\s*[,}]|\s*$))',
                text, _re.DOTALL | _re.IGNORECASE
            )
            if m:
                text = m.group(1)

    # 2. Supprimer les blocs JSON embarqués au milieu du texte (ex: texte {"key":"val"} texte)
    def _unwrap_embedded(m: "_re.Match") -> str:
        fragment = m.group(0)
        try:
            obj = _json.loads(fragment)
            if isinstance(obj, dict):
                for key in ("response_text", "responsetext", "response", "text", "content"):
                    val = obj.get(key)
                    if isinstance(val, str) and len(val) > 10:
                        return val
        except Exception:
            pass
        return ""  # Supprimer le fragment JSON non parseable

    text = _re.sub(r'\{[^{}]{10,}\}', _unwrap_embedded, text, flags=_re.DOTALL)

    # 3. Convertir les \\n et \\t littéraux en vrais caractères
    text = text.replace("\\n", "\n").replace("\\t", "\t")

    # 4a. Dédupliquer les paragraphes (séparés par double saut de ligne)
    paragraphs = text.split("\n\n")
    seen_p: set = set()
    unique_p: list = []
    for p in paragraphs:
        key = p.strip()
        if key and key not in seen_p:
            seen_p.add(key)
            unique_p.append(p)
    text = "\n\n".join(unique_p)

    # 4b. Dédupliquer les lignes répétées au sein des paragraphes
    lines = text.split("\n")
    seen_l: set = set()
    unique_l: list = []
    for line in lines:
        key = line.strip()
        if not key:
            unique_l.append(line)  # Conserver les lignes vides pour la mise en forme
        elif key not in seen_l:
            seen_l.add(key)
            unique_l.append(line)
    text = "\n".join(unique_l)

    # 5. Filtre définitif anti-numéros de téléphone
    text = _strip_phones(text)

    return text.strip()


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

        # Les vétérinaires partenaires sont envoyés dans partner_vets (champ séparé)
        # et affichés en cards cliquables côté frontend — jamais dans le texte.

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
async def chat(request: ChatRequest):
    """Endpoint conversationnel principal de DoctoAgent / Cheebo."""
    session_id   = request.session_id or str(uuid.uuid4())
    history      = request.history
    user_message = request.message.strip()

    logger.info(f"[Chat {session_id[:8]}] User: '{user_message[:60]}'")

    # Cas 1 : Premier message vide → salutation (pas de sauvegarde)
    if not history:
        return ChatResponse(
            session_id=session_id,
            response=GREETING,
            agent_type="GREETING",
        )

    try:
        # Accumuler tous les messages utilisateur → contexte médical complet à travers les échanges
        analysis_text = _build_accumulated_context(user_message, history)

        # Analyse NLP
        nlp_result = nlp_pipeline.process(analysis_text)
        nlp_dict = nlp_result if isinstance(nlp_result, dict) else (
            nlp_result.model_dump() if hasattr(nlp_result, "model_dump") else vars(nlp_result)
        )
        entities         = nlp_dict.get("entities", [])
        intent           = nlp_dict.get("intent", "")
        urgency_from_nlp = nlp_dict.get("urgency_label", "LOW")
        has_symptom      = (
            any(e.get("label") == "SYMPTOM" for e in entities)
            or _has_symptom_keywords(analysis_text)
            or urgency_from_nlp in ("MODERATE", "HIGH", "CRITICAL")
        )
        duree_detected   = any(e.get("label") == "DUREE" for e in entities)

        # ── Signaux de routage ─────────────────────────────────────────
        language              = nlp_dict.get("language", "fr")
        # Symptôme dans le message ACTUEL (pas dans l'historique accumulé)
        has_symptom_now       = _has_symptom_keywords(user_message)
        # Urgence détectée (intent ou NLP)
        is_emergency          = intent == "emergency" or urgency_from_nlp in ("CRITICAL", "HIGH")
        # L'agent vient de poser une question de suivi structurée
        is_answering_followup = _last_agent_was_question(history)
        # La conversation a déjà un contexte médical (symptômes dans l'historique)
        has_medical_context   = has_symptom and any(m.role == "agent" for m in history)

        # ── Salutation / politesse pure → jamais pipeline ─────────────
        is_greeting_only  = user_message.strip().lower() in _SOCIAL_ONLY_MESSAGES
        # Acquittement : amélioration, remerciement, clôture, confirmation d'action
        is_acknowledgment = _is_acknowledgment(user_message)

        # ── Décision : pipeline nécessaire ? ───────────────────────────
        # Pipeline si : urgence OU nouveau symptôme OU réponse à une question de suivi
        # SAUF : salutation pure OU acquittement sans nouveau symptôme ni urgence
        # (ex: "c'est mieux merci" → is_answering_followup peut être True car il y
        #  avait une question ouverte, mais c'est clairement une clôture → pas pipeline)
        go_to_pipeline = (
            (is_emergency or has_symptom_now or is_answering_followup)
            and not is_greeting_only
            and not (is_acknowledgment and not has_symptom_now and not is_emergency)
        )

        if not go_to_pipeline:
            # Acquittement (j'ai contacté le vet, il va mieux, on y va…)
            if _is_acknowledgment(user_message):
                reply = await groq_guard.contextual_reply(user_message, language, history)
                if not reply:
                    reply = _acknowledgment_reply(language)
                await _save_to_mongo(
                    session_id, user_message, reply, "GREETING",
                    None, None, nlp_dict, {},
                )
                return ChatResponse(
                    session_id = session_id,
                    response   = reply,
                    agent_type = "GREETING",
                )

            # Question ou commentaire dans un contexte médical existant
            # ("c'est grave ?", "que faire à la maison ?", "merci", etc.)
            if has_medical_context:
                reply = await groq_guard.contextual_reply(user_message, language, history)
                if not reply:
                    reply = _no_symptom_reply(language, entities)
                await _save_to_mongo(
                    session_id, user_message, reply, "QUESTION",
                    None, None, nlp_dict, {},
                )
                return ChatResponse(
                    session_id = session_id,
                    response   = reply,
                    agent_type = "QUESTION",
                )

            # Aucun contexte médical → demander les symptômes
            reply = await groq_guard.fallback_response(
                user_message = user_message,
                language     = language,
                entities     = entities,
                history      = history,
            )
            if not reply:
                reply = _no_symptom_reply(language, entities)
            await _save_to_mongo(
                session_id, user_message, reply, "QUESTION",
                None, None, nlp_dict, {},
            )
            return ChatResponse(
                session_id = session_id,
                response   = reply,
                agent_type = "QUESTION",
            )

        # ── Question animal avant pipeline ─────────────────────────────
        # Seulement si nouveau symptôme (pas urgence, pas réponse à suivi)
        if has_symptom_now and not is_emergency:
            animal_detected = any(e.get("label") == "ANIMAL" for e in entities)
            if (
                not animal_detected
                and not _info_already_in_message(analysis_text, "animal")
                and not _already_asked(history, "animal")
            ):
                prefix = {
                    "fr": "Je vois que votre compagnon présente des symptômes. Pour vous donner les meilleurs conseils, j'aurais besoin de savoir :\n\n",
                    "en": "I see your companion is showing symptoms. To give you the best advice, I need to know:\n\n",
                    "ar": "أرى أن حيوانك يعاني من أعراض. لأقدم لك أفضل النصائح، أحتاج أن أعرف:\n\n",
                }.get(language, "Je vois que votre compagnon présente des symptômes. Pour vous donner les meilleurs conseils, j'aurais besoin de savoir :\n\n")
                reply = prefix + _follow_up_q("animal", language)
                await _save_to_mongo(
                    session_id, user_message, reply, "QUESTION",
                    None, None, nlp_dict, {},
                )
                return ChatResponse(
                    session_id = session_id,
                    response   = reply,
                    agent_type = "QUESTION",
                )

        # Pipeline multi-agents
        loop = asyncio.get_running_loop()
        final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)

        level = final_response.get("urgency", {}).get("level", "LOW")
        vets  = _get_partner_vets(level)

        # ── Génération de la réponse finale ───────────────────────────
        # Architecture :
        #   1. Les agents (SynthesisAgent) ont produit un texte ?
        #      OUI → Groq fait uniquement un quality_check (ton / intro)
        #      NON → Groq génère la réponse complète à la place des agents
        def _agent_text(data: dict) -> str:
            synthesis = data.get("synthesis", {})
            raw = synthesis.get("response_text", "")
            text = _clean_agent_text(raw)
            if text and len(text) > 50:
                return text
            return ""

        async def _build_final_text(data: dict, msg: str, lvl: str) -> str:
            agent_out = _agent_text(data)
            if agent_out:
                # Agents ont répondu → Groq valide seulement le ton
                return await groq_guard.quality_check(agent_out, msg, lvl)
            else:
                # Agents ont échoué → Groq génère à la place (style Cheebo)
                return await groq_guard.generate_response(data, msg)

        # Cas 3 : HIGH/CRITICAL → urgence
        if level in ("CRITICAL", "HIGH"):
            chat_text = await _build_final_text(final_response, user_message, level)
            await _save_to_mongo(
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

        # Cas 4 : MODERATE → questions de suivi si info manquante, sinon analyse
        if level == "MODERATE":
            for key in ("duree", "repas", "comportement"):
                if key == "duree" and duree_detected:
                    continue
                if _info_already_in_message(analysis_text, key):
                    continue
                if not _already_asked(history, key):
                    prefix = {
                        "fr": "Je comprends, votre animal ne va pas très bien. Pour mieux évaluer la situation, j'aurais besoin d'une précision :\n\n",
                        "en": "I understand your pet isn't feeling well. To better assess the situation, I need one more detail:\n\n",
                        "ar": "أفهم أن حيوانك لا يشعر بتحسن. لتقييم الوضع بشكل أفضل، أحتاج إلى معلومة إضافية:\n\n",
                    }.get(language, "Je comprends, votre animal ne va pas très bien. Pour mieux évaluer la situation, j'aurais besoin d'une précision :\n\n")
                    reply = prefix + _follow_up_q(key, language)
                    await _save_to_mongo(
                        session_id, user_message, reply, "QUESTION",
                        level, None, nlp_dict, final_response,
                    )
                    return ChatResponse(
                        session_id    = session_id,
                        response      = reply,
                        agent_type    = "QUESTION",
                        urgency_label = level,
                    )
            chat_text = await _build_final_text(final_response, user_message, level)
            await _save_to_mongo(
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

        # Cas 5 : LOW → analyse directe
        chat_text = await _build_final_text(final_response, user_message, level)
        await _save_to_mongo(
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


# ──────────────────────────────────────────────────────────────────
# ANALYSE D'IMAGE — Vision Groq
# ──────────────────────────────────────────────────────────────────

async def _describe_image_with_groq(image_bytes: bytes, mime_type: str) -> str:
    """Analyse l'image avec Groq Vision et retourne une description médicale."""
    import os
    from groq import AsyncGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Image reçue — analyse visuelle indisponible (clé API manquante)."

    b64 = base64.b64encode(image_bytes).decode()
    client = AsyncGroq(api_key=api_key)

    try:
        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "Tu es un assistant vétérinaire. Analyse cette photo d'un animal de compagnie. "
                                "Décris en 2 à 3 phrases ce que tu observes de manière médicalement pertinente : "
                                "espèce et race probable, posture, état général visible, "
                                "signes de détresse ou d'inconfort, anomalies physiques visibles "
                                "(plaie, gonflement, pelage, yeux, membres, etc.). "
                                "Sois précis et factuel. "
                                "Si l'image ne montre pas clairement un animal ou ses symptômes, dis-le simplement."
                            ),
                        },
                    ],
                }],
                max_tokens=250,
            ),
            timeout=14.0,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning(f"[ChatImage] Groq Vision échouée : {e}")
        return "Image reçue — impossible d'obtenir une description visuelle automatique."


@router.post("/chat/image", response_model=ChatResponse)
async def chat_with_image(
    images       : List[UploadFile] = File(...),
    message      : str              = Form(""),
    session_id   : str              = Form(None),
    history_json : str              = Form("[]"),
):
    """
    Endpoint conversationnel avec une ou plusieurs images.
    Chaque image est analysée par Groq Vision ; les descriptions sont
    injectées dans le pipeline multi-agents avec le texte de l'utilisateur.
    """
    session_id   = session_id or str(uuid.uuid4())
    user_message = message.strip()

    # Parse history
    try:
        history_raw = json_lib.loads(history_json)
        history     = [ChatMessage(**m) for m in history_raw if "role" in m and "content" in m]
    except Exception:
        history = []

    logger.info(f"[ChatImage {session_id[:8]}] {len(images)} photo(s) + message='{user_message[:40]}'")

    # Lire et encoder toutes les images
    all_bytes  = [await img.read() for img in images]
    all_mimes  = [img.content_type or "image/jpeg" for img in images]
    all_base64 = [base64.b64encode(b).decode("utf-8") for b in all_bytes]

    # Analyser chaque image en parallèle avec Groq Vision
    descs = await asyncio.gather(*[
        _describe_image_with_groq(b, m) for b, m in zip(all_bytes, all_mimes)
    ])
    if len(descs) == 1:
        visual_desc = descs[0]
    else:
        visual_desc = " | ".join(f"Photo {i+1}: {d}" for i, d in enumerate(descs))
    logger.info(f"[ChatImage {session_id[:8]}] Vision: '{visual_desc[:80]}'")

    # Récupérer le contexte textuel accumulé des messages précédents (hors images)
    prior_text_parts = [
        m.content.strip() for m in history
        if m.role == "user" and m.content.strip() and not m.has_images
    ]
    prior_text = ". ".join(prior_text_parts) if prior_text_parts else ""

    # Construire le texte d'analyse : contexte antérieur + message actuel + vision
    parts = []
    if prior_text:
        parts.append(prior_text)
    if user_message:
        parts.append(user_message)
    parts.append(f"[Observation visuelle de l'animal : {visual_desc}]")
    analysis_text = "\n".join(parts)

    # Message utilisateur affiché (sans la description technique)
    display_message = user_message or "Photo de l'animal envoyée pour analyse."

    try:
        nlp_result = nlp_pipeline.process(analysis_text)
        nlp_dict   = nlp_result if isinstance(nlp_result, dict) else (
            nlp_result.model_dump() if hasattr(nlp_result, "model_dump") else vars(nlp_result)
        )
        level = "LOW"

        loop           = asyncio.get_running_loop()
        final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)
        level          = final_response.get("urgency", {}).get("level", "LOW")
        vets           = _get_partner_vets(level)

        # Même pattern : agents répondent → quality_check ; agents échouent → Groq génère
        agent_out = _clean_agent_text(final_response.get("synthesis", {}).get("response_text", ""))
        if agent_out and len(agent_out) > 50:
            chat_text = await groq_guard.quality_check(agent_out, analysis_text, level)
        else:
            chat_text = await groq_guard.generate_response(final_response, analysis_text)

        # Préfixer avec la description visuelle
        visual_prefix = f"📸 **Analyse de la photo**\n_{visual_desc}_\n\n"
        chat_text = visual_prefix + chat_text

        await _save_to_mongo(
            session_id, display_message, chat_text,
            "ANALYSIS" if level not in ("CRITICAL", "HIGH") else "EMERGENCY",
            level, vets, nlp_dict, final_response,
            images_base64=all_base64,
        )

        return ChatResponse(
            session_id    = session_id,
            response      = chat_text,
            agent_type    = "ANALYSIS" if level not in ("CRITICAL", "HIGH") else "EMERGENCY",
            urgency_label = level,
            full_data     = final_response,
            partner_vets  = vets,
        )

    except Exception as e:
        logger.error(f"[ChatImage {session_id[:8]}] Erreur pipeline : {e}", exc_info=True)
        fallback = (
            f"📸 **Photo analysée**\n_{visual_desc}_\n\n"
            "Je n'ai pas pu effectuer une analyse complète. "
            "Pouvez-vous décrire en mots les symptômes de votre animal ?"
        )
        return ChatResponse(
            session_id = session_id,
            response   = fallback,
            agent_type = "QUESTION",
        )


# ──────────────────────────────────────────────────────────────────
# ANALYSE VIDÉO — Extraction frames + Vision Groq
# ──────────────────────────────────────────────────────────────────

def _try_ffmpeg_frames(path: str, n_frames: int) -> list:
    """
    Extraction via imageio-ffmpeg (binaire ffmpeg auto-téléchargé).
    Fonctionne avec tous les formats : MP4, MOV, AVI, MKV, WEBM…
    """
    import json
    import subprocess
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return []

    # Sonde la durée de la vidéo
    ffprobe_exe = ffmpeg_exe.replace("ffmpeg", "ffprobe")
    duration = 10.0
    try:
        raw = subprocess.check_output(
            [ffprobe_exe, "-v", "quiet", "-print_format", "json", "-show_streams", path],
            timeout=10, stderr=subprocess.DEVNULL,
        )
        info = json.loads(raw)
        duration = float(next(
            (s["duration"] for s in info.get("streams", []) if s.get("codec_type") == "video"),
            10.0,
        ))
    except Exception:
        pass

    frames = []
    for i in range(n_frames):
        ts = duration * i / n_frames
        try:
            jpeg = subprocess.check_output(
                [
                    ffmpeg_exe, "-ss", f"{ts:.3f}", "-i", path,
                    "-frames:v", "1",
                    "-vf", "scale='min(800,iw)':-2",
                    "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "5",
                    "pipe:1",
                ],
                timeout=15, stderr=subprocess.DEVNULL,
            )
            if jpeg:
                frames.append(jpeg)
        except Exception:
            pass
    return frames


def _try_cv2_frames(path: str, n_frames: int) -> list:
    """Extraction via opencv-python-headless (fallback si ffmpeg indisponible)."""
    try:
        import cv2
    except ImportError:
        return []
    cap   = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total == 0:
        cap.release()
        return []
    n       = min(n_frames, total)
    indices = [int(i * total / n) for i in range(n)]
    frames  = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if not ret:
            continue
        h, w = frame.shape[:2]
        if w > 800:
            frame = cv2.resize(frame, (800, int(h * 800 / w)))
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        frames.append(buf.tobytes())
    cap.release()
    return frames


def _extract_video_frames_sync(video_bytes: bytes, n_frames: int = 5, ext: str = ".mp4") -> list:
    """
    Extrait n frames régulièrement espacées d'une vidéo.
    Stratégie 1 : imageio-ffmpeg (supporte MP4, MOV, AVI, MKV…).
    Stratégie 2 : opencv-python-headless (fallback).
    Fonction synchrone — doit être exécutée via run_in_executor.
    """
    import os
    import tempfile

    suffix = ext if ext.startswith(".") else f".{ext}"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(video_bytes)
        tmp_path = tmp.name

    try:
        frames = _try_ffmpeg_frames(tmp_path, n_frames)
        if not frames:
            frames = _try_cv2_frames(tmp_path, n_frames)
        return frames
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/chat/video", response_model=ChatResponse)
async def chat_with_video(
    video        : UploadFile = File(...),
    message      : str        = Form(""),
    session_id   : str        = Form(None),
    history_json : str        = Form("[]"),
):
    """
    Endpoint conversationnel avec une courte vidéo de l'animal.
    Extrait 5 frames, analyse chacune via Groq Vision, synthétise temporellement,
    puis déclenche le pipeline multi-agents identiquement à /chat/image.
    Formats acceptés : MP4, MOV, AVI, MKV. Taille max : 50 MB.
    """
    session_id   = session_id or str(uuid.uuid4())
    user_message = message.strip()

    try:
        history_raw = json_lib.loads(history_json)
        history     = [ChatMessage(**m) for m in history_raw if "role" in m and "content" in m]
    except Exception:
        history = []

    logger.info(f"[ChatVideo {session_id[:8]}] '{video.filename}' + msg='{user_message[:40]}'")

    video_bytes = await video.read()
    if len(video_bytes) > 50 * 1024 * 1024:
        return ChatResponse(
            session_id = session_id,
            response   = (
                "⚠️ Vidéo trop volumineuse (50 MB maximum). "
                "Envoyez une vidéo de moins de 30 secondes ou quelques photos à la place."
            ),
            agent_type = "QUESTION",
        )

    # ── Extraction des frames dans un thread (cv2 est synchrone) ──────────
    # Extraire l'extension réelle du fichier uploadé (.mov, .mp4, .avi…)
    import os as _os
    raw_ext = _os.path.splitext(video.filename or "video.mp4")[1].lower()
    video_ext = raw_ext if raw_ext in (".mp4", ".mov", ".avi", ".mkv", ".webm", ".3gp") else ".mp4"

    loop = asyncio.get_running_loop()
    try:
        frames_bytes: list = await asyncio.wait_for(
            loop.run_in_executor(None, _extract_video_frames_sync, video_bytes, 3, video_ext),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        frames_bytes = []
        logger.warning(f"[ChatVideo {session_id[:8]}] Extraction frames timeout")
    except Exception as exc:
        frames_bytes = []
        logger.warning(f"[ChatVideo {session_id[:8]}] Extraction frames erreur : {exc}")

    if not frames_bytes:
        return ChatResponse(
            session_id = session_id,
            response   = (
                "📹 Vidéo reçue mais impossible d'en extraire les images. "
                "Vérifiez le format (MP4, MOV, AVI) ou envoyez quelques photos à la place."
            ),
            agent_type = "QUESTION",
        )

    logger.info(f"[ChatVideo {session_id[:8]}] {len(frames_bytes)} frames extraites")

    # ── Analyse visuelle de chaque frame en parallèle ─────────────────────
    descs: list = list(await asyncio.gather(*[
        _describe_image_with_groq(b, "image/jpeg") for b in frames_bytes
    ]))

    # ── Synthèse temporelle via Groq ───────────────────────────────────────
    temporal_desc = await groq_guard.synthesize_video_frames(descs, language="fr")
    logger.info(f"[ChatVideo {session_id[:8]}] Synthèse: '{temporal_desc[:80]}'")

    # ── Contexte textuel accumulé (hors messages avec images) ─────────────
    prior_text_parts = [
        m.content.strip() for m in history
        if m.role == "user" and m.content.strip() and not m.has_images
    ]
    prior_text = ". ".join(prior_text_parts) if prior_text_parts else ""

    parts = []
    if prior_text:
        parts.append(prior_text)
    if user_message:
        parts.append(user_message)
    parts.append(f"[Observation vidéo de l'animal : {temporal_desc}]")
    analysis_text = "\n".join(parts)

    display_message = user_message or "Vidéo de l'animal envoyée pour analyse."

    try:
        nlp_result = nlp_pipeline.process(analysis_text)
        nlp_dict   = nlp_result if isinstance(nlp_result, dict) else (
            nlp_result.model_dump() if hasattr(nlp_result, "model_dump") else vars(nlp_result)
        )
        language = nlp_dict.get("language", "fr")

        # Mettre à jour la synthèse vidéo avec la bonne langue
        if language != "fr":
            temporal_desc = await groq_guard.synthesize_video_frames(descs, language=language)

        final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)
        level          = final_response.get("urgency", {}).get("level", "LOW")
        vets           = _get_partner_vets(level)

        agent_out = _clean_agent_text(final_response.get("synthesis", {}).get("response_text", ""))
        if agent_out and len(agent_out) > 50:
            chat_text = await groq_guard.quality_check(agent_out, analysis_text, level)
        else:
            chat_text = await groq_guard.generate_response(final_response, analysis_text)

        video_prefix = (
            f"🎥 **Analyse de la vidéo** ({len(frames_bytes)} images analysées)\n"
            f"_{temporal_desc}_\n\n"
        )
        chat_text = video_prefix + chat_text

        await _save_to_mongo(
            session_id, display_message, chat_text,
            "ANALYSIS" if level not in ("CRITICAL", "HIGH") else "EMERGENCY",
            level, vets, nlp_dict, final_response,
        )

        return ChatResponse(
            session_id    = session_id,
            response      = chat_text,
            agent_type    = "ANALYSIS" if level not in ("CRITICAL", "HIGH") else "EMERGENCY",
            urgency_label = level,
            full_data     = final_response,
            partner_vets  = vets,
        )

    except Exception as e:
        logger.error(f"[ChatVideo {session_id[:8]}] Erreur pipeline : {e}", exc_info=True)
        return ChatResponse(
            session_id = session_id,
            response   = (
                f"🎥 **Vidéo analysée**\n_{temporal_desc}_\n\n"
                "Je n'ai pas pu effectuer une analyse complète. "
                "Pouvez-vous décrire en mots les symptômes de votre animal ?"
            ),
            agent_type = "QUESTION",
        )
