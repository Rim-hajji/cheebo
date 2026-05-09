"""
Cheebo — MongoDB Connection (Motor async)
==========================================
Connexion à MongoDB locale via Motor (driver async).
Collections : conversations, analysis_logs, partner_vets, api_logs

URI par défaut : mongodb://localhost:27017/cheebo_db
Peut être surchargé via la variable d'environnement MONGO_URI.
"""

import logging
import os
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger("cheebo.database")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = os.getenv("MONGO_DB",  "cheebo_db")

_client: AsyncIOMotorClient = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        logger.info(f"MongoDB connecté : {MONGO_URI}/{DB_NAME}")
    return _client


def get_db():
    return get_client()[DB_NAME]


# ── Raccourcis vers les collections ─────────────────────────────────
def conversations():
    return get_db()["conversations"]

def analysis_logs():
    return get_db()["analysis_logs"]

def partner_vets():
    return get_db()["partner_vets"]

def api_logs():
    return get_db()["api_logs"]


# ── Initialisation (indexes + seed vets) ────────────────────────────
async def init_db():
    """Crée les index et insère les vets partenaires si la collection est vide."""
    db = get_db()

    # Index sur session_id pour les conversations
    await db["conversations"].create_index("session_id", unique=True)
    await db["conversations"].create_index("updated_at")

    # Index sur analysis_logs
    await db["analysis_logs"].create_index("session_id")
    await db["analysis_logs"].create_index("created_at")
    await db["analysis_logs"].create_index("urgency_level")

    # Index api_logs
    await db["api_logs"].create_index("created_at")

    # Seed des vétérinaires partenaires si vide
    count = await db["partner_vets"].count_documents({})
    if count == 0:
        await db["partner_vets"].insert_many([
            {
                "name"       : "Clinique Vétérinaire El Menzah",
                "phone"      : "+216 71 234 567",
                "address"    : "Rue des Roses, El Menzah 6, Tunis",
                "specialties": ["urgences 24/7", "chirurgie", "médecine interne"],
                "available"  : True,
                "emergency"  : True,
                "created_at" : datetime.now(timezone.utc),
            },
            {
                "name"       : "Cabinet Vétérinaire Les Berges du Lac",
                "phone"      : "+216 71 345 678",
                "address"    : "Les Berges du Lac II, Tunis",
                "specialties": ["urgences", "dermatologie", "ophtalmologie"],
                "available"  : True,
                "emergency"  : True,
                "created_at" : datetime.now(timezone.utc),
            },
            {
                "name"       : "VetCare Centre — Ariana",
                "phone"      : "+216 71 456 789",
                "address"    : "Avenue de la République, Ariana",
                "specialties": ["chirurgie orthopédique", "neurologie"],
                "available"  : True,
                "emergency"  : False,
                "created_at" : datetime.now(timezone.utc),
            },
        ])
        logger.info("Vétérinaires partenaires initialisés dans MongoDB")

    logger.info("MongoDB — index et seed OK")
