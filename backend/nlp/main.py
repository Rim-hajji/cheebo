"""
DoctoAgent API v2 — FastAPI
============================
API REST exposant le pipeline NLP DoctoAgent.

Endpoints :
    GET  /health         → Statut de l'API
    POST /analyze        → Analyse complète d'un message
    POST /emergency      → Détection rapide d'urgence
    POST /translate      → Traduction simple
    GET  /history        → Toutes les consultations
    GET  /history/{id}   → Historique par utilisateur
    DELETE /history      → Vider l'historique

Lancement :
    py main.py
    → http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline import nlp_pipeline

# ──────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "DoctoAgent API",
    description = "API NLP vétérinaire pour la plateforme Cheebo (multilingue EN/FR/AR)",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ──────────────────────────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    text    : str = Field(..., description="Message vétérinaire à analyser", min_length=2, max_length=1000)
    user_id : Optional[str] = None
    pet_id  : Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "text"   : "My dog has been vomiting since yesterday",
                "user_id": "user_123",
                "pet_id" : "pet_456",
            }
        }


class EntityResponse(BaseModel):
    text       : str
    label      : str
    confidence : float = 0.0


class AnalyzeResponse(BaseModel):
    consultation_id      : str
    timestamp            : str
    original_text        : str
    translated_text      : str   = ""
    language             : str
    was_translated       : bool  = False
    intent               : str
    intent_confidence    : float
    urgency_label        : str
    urgency_score        : int
    urgency_confidence   : float
    entities             : List[EntityResponse]
    ner_source           : str


class EmergencyRequest(BaseModel):
    text    : str = Field(..., min_length=2, max_length=1000)
    user_id : Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "text": "My dog collapsed and is not breathing"
            }
        }


class EmergencyResponse(BaseModel):
    is_emergency  : bool
    urgency_label : str
    urgency_score : int
    language      : str
    message       : str
    call_vet_now  : bool


class TranslateRequest(BaseModel):
    text          : str
    source_lang   : Optional[str] = None
    target_lang   : str = "en"


class TranslateResponse(BaseModel):
    original_text   : str
    translated_text : str
    source_language : str
    target_language : str


class HealthResponse(BaseModel):
    status        : str
    version       : str
    models_loaded : dict
    timestamp     : str


# ──────────────────────────────────────────────────────────────────
# HISTORIQUE
# ──────────────────────────────────────────────────────────────────
consultation_history = []


# ──────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Système"])
async def root():
    """Page d'accueil de l'API."""
    return {
        "service" : "DoctoAgent API",
        "version" : "2.0.0",
        "docs"    : "/docs",
        "status"  : "online",
    }


@app.get("/health", response_model=HealthResponse, tags=["Système"])
async def health_check():
    """Vérifie le statut de l'API et des modèles chargés."""
    return HealthResponse(
        status        = "ok",
        version       = "2.0.0",
        models_loaded = {
            "intent_model"      : nlp_pipeline.classifier         is not None,
            "urgency_model"     : nlp_pipeline.urgency_model      is not None,
            "ner_vetbert"       : nlp_pipeline.ner_vetbert_model  is not None,
            "ner_vetbert"       : nlp_pipeline.ner_vetbert_model  is not None,
        },
        timestamp = datetime.now().isoformat(),
    )


@app.post("/analyze", response_model=AnalyzeResponse, tags=["Analyse"])
async def analyze(request: AnalyzeRequest):
    """
    Analyse complète d'un message vétérinaire.

    **Fonctionnalités :**
    - Détection automatique de la langue
    - Traduction si arabe (ou autre langue non native)
    - Classification d'intent (describe_symptom, ask_advice, emergency, follow_up)
    - Classification d'urgence (LOW, MODERATE, HIGH, CRITICAL)
    - Reconnaissance d'entités (ANIMAL, SYMPTOM, DUREE, BODY_PART)
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte ne peut pas être vide.")

    try:
        result = nlp_pipeline.process(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur pipeline NLP : " + str(e))

    consultation_id = str(uuid.uuid4())[:8]
    timestamp       = datetime.now().isoformat()

    # Sauvegarder dans l'historique
    consultation_history.append({
        "consultation_id": consultation_id,
        "timestamp"      : timestamp,
        "user_id"        : request.user_id,
        "pet_id"         : request.pet_id,
        "text"           : request.text,
        "language"       : result.language,
        "urgency_label"  : result.urgency_label,
        "intent"         : result.intent,
    })

    return AnalyzeResponse(
        consultation_id      = consultation_id,
        timestamp            = timestamp,
        original_text        = result.original_text,
        translated_text      = result.translated_text,
        language             = result.language,
        was_translated       = result.was_translated,
        intent               = result.intent,
        intent_confidence    = round(result.intent_confidence, 3),
        urgency_label        = result.urgency_label,
        urgency_score        = result.urgency_score,
        urgency_confidence   = round(result.urgency_confidence, 3),
        entities             = [
            EntityResponse(
                text       = e.get("text", ""),
                label      = e.get("label", ""),
                confidence = e.get("confidence", 0.0),
            )
            for e in result.entities
        ],
        ner_source           = result.ner_source,
    )


@app.post("/emergency", response_model=EmergencyResponse, tags=["Urgence"])
async def emergency_check(request: EmergencyRequest):
    """
    Détection rapide d'urgence vitale.
    Réponse optimisée pour les cas critiques.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte ne peut pas être vide.")

    try:
        result = nlp_pipeline.process(request.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erreur pipeline NLP : " + str(e))

    is_emergency = result.urgency_label in ["HIGH", "CRITICAL"]
    call_vet_now = result.urgency_label == "CRITICAL"

    messages = {
        "CRITICAL": "🚨 URGENCE VITALE — Allez immédiatement aux urgences vétérinaires !",
        "HIGH"    : "⚠️ URGENT — Contactez un vétérinaire dans les 2 heures.",
        "MODERATE": "📋 Consultez un vétérinaire dans les 24h.",
        "LOW"     : "ℹ️ Pas d'urgence immédiate détectée.",
    }

    return EmergencyResponse(
        is_emergency  = is_emergency,
        urgency_label = result.urgency_label,
        urgency_score = result.urgency_score,
        language      = result.language,
        message       = messages.get(result.urgency_label, ""),
        call_vet_now  = call_vet_now,
    )


@app.post("/translate", response_model=TranslateResponse, tags=["Traduction"])
async def translate(request: TranslateRequest):
    """
    Traduit un texte vers la langue cible.
    Utile pour traduire des messages utilisateurs avant traitement.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte ne peut pas être vide.")

    if nlp_pipeline.translator is None:
        raise HTTPException(status_code=503, detail="Service de traduction indisponible.")

    source = request.source_lang or nlp_pipeline.detect_language(request.text)
    translated = nlp_pipeline.translate_to_english(request.text, source_lang=source)

    return TranslateResponse(
        original_text   = request.text,
        translated_text = translated,
        source_language = source,
        target_language = request.target_lang,
    )


@app.get("/history", tags=["Historique"])
async def get_history(limit: int = 10):
    """Récupère les dernières consultations."""
    return {
        "total"        : len(consultation_history),
        "consultations": consultation_history[-limit:][::-1],
    }


@app.get("/history/{user_id}", tags=["Historique"])
async def get_user_history(user_id: str, limit: int = 10):
    """Récupère l'historique d'un utilisateur."""
    user_consultations = [
        c for c in consultation_history
        if c.get("user_id") == user_id
    ]
    return {
        "user_id"      : user_id,
        "total"        : len(user_consultations),
        "consultations": user_consultations[-limit:][::-1],
    }


@app.delete("/history", tags=["Historique"])
async def clear_history():
    """Vide l'historique des consultations."""
    consultation_history.clear()
    return {"message": "Historique vidé avec succès."}


# ──────────────────────────────────────────────────────────────────
# LANCEMENT
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host      = "0.0.0.0",
        port      = 8000,
        reload    = False,
        log_level = "info",
    )