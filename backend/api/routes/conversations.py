"""
Cheebo — Routes /conversations
================================
Historique des conversations stocké dans MongoDB.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.mongo import conversations as conv_col, analysis_logs as logs_col

router = APIRouter()


class MessageOut(BaseModel):
    role         : str
    content      : str
    agent_type   : Optional[str] = None
    urgency_label: Optional[str] = None
    timestamp    : Optional[str] = None
    partner_vets : Optional[list] = None
    image_base64  : Optional[str]       = None
    images_base64 : Optional[List[str]] = None


class ConversationSummary(BaseModel):
    session_id   : str
    title        : str
    language     : Optional[str] = "fr"
    message_count: int
    created_at   : Optional[str] = None
    updated_at   : Optional[str] = None


class ConversationDetail(ConversationSummary):
    messages: List[MessageOut] = []


def _iso(dt) -> Optional[str]:
    return dt.isoformat() if dt else None


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(limit: int = 50):
    """Liste les conversations triées par date décroissante."""
    cursor = conv_col().find({}, {"messages": 0}).sort("updated_at", -1).limit(limit)
    result = []
    async for doc in cursor:
        doc.pop("_id", None)
        result.append(ConversationSummary(
            session_id    = doc.get("session_id", ""),
            title         = doc.get("title", "Conversation"),
            language      = doc.get("language", "fr"),
            message_count = doc.get("message_count", 0),
            created_at    = _iso(doc.get("created_at")),
            updated_at    = _iso(doc.get("updated_at")),
        ))
    return result


@router.get("/conversations/{session_id}", response_model=ConversationDetail)
async def get_conversation(session_id: str):
    """Retourne une conversation complète avec tous ses messages."""
    doc = await conv_col().find_one({"session_id": session_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    doc.pop("_id", None)
    messages = [
        MessageOut(
            role          = m.get("role", ""),
            content       = m.get("content", ""),
            agent_type    = m.get("agent_type"),
            urgency_label = m.get("urgency_label"),
            timestamp     = _iso(m.get("timestamp")),
            partner_vets  = m.get("partner_vets"),
            image_base64  = m.get("image_base64"),
            images_base64 = m.get("images_base64"),
        )
        for m in doc.get("messages", [])
    ]
    return ConversationDetail(
        session_id    = doc["session_id"],
        title         = doc.get("title", "Conversation"),
        language      = doc.get("language", "fr"),
        message_count = doc.get("message_count", 0),
        created_at    = _iso(doc.get("created_at")),
        updated_at    = _iso(doc.get("updated_at")),
        messages      = messages,
    )


@router.delete("/conversations/{session_id}", status_code=204)
async def delete_conversation(session_id: str):
    """Supprime une conversation et tous ses messages."""
    result = await conv_col().delete_one({"session_id": session_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")


@router.get("/db-test")
async def db_test():
    """Vérifie que MongoDB lit et écrit correctement (endpoint de diagnostic)."""
    import uuid
    test_id = f"__test__{uuid.uuid4().hex[:8]}"
    try:
        # Écriture
        await conv_col().insert_one({
            "session_id"   : test_id,
            "title"        : "Test de diagnostic",
            "language"     : "fr",
            "message_count": 0,
            "created_at"   : datetime.now(timezone.utc),
            "updated_at"   : datetime.now(timezone.utc),
            "messages"     : [],
        })
        # Lecture
        doc = await conv_col().find_one({"session_id": test_id})
        # Nettoyage
        await conv_col().delete_one({"session_id": test_id})

        if doc:
            return {"status": "ok", "message": "MongoDB lecture/écriture fonctionnelle"}
        return {"status": "error", "message": "Document inséré mais non retrouvé"}
    except Exception as e:
        return {"status": "error", "message": str(e), "type": type(e).__name__}


_URGENCY_SCORES = {"LOW": 1, "MODERATE": 4, "HIGH": 7, "CRITICAL": 10}


@router.get("/analysis-history")
async def get_analysis_history(limit: int = 100):
    """Retourne l'historique unifié : analyses /analyze + conversations chat.
    Une seule entrée par conversation (session_id), urgence maximale atteinte."""
    result = []

    # ── 1. Entrées depuis /analyze (source = "analyze") ──────────────
    cursor = logs_col().find({"source": "analyze"}).sort("date", -1).limit(limit)
    async for doc in cursor:
        result.append({
            "item_id"      : str(doc["_id"]),
            "date"         : _iso(doc.get("date")),
            "text"         : doc.get("text", ""),
            "urgency_label": doc.get("urgency_label", "LOW"),
            "score"        : doc.get("score", 0),
        })

    # ── 2. Conversations chat — une entrée par session_id ────────────
    # Agrégation : urgence maximale + date de dernière activité par session
    pipeline = [
        {"$match": {"source": {"$ne": "analyze"}, "urgency_level": {"$nin": [None, ""]}}},
        {"$group": {
            "_id"         : "$session_id",
            "max_urgency" : {"$max": "$urgency_level"},
            "last_date"   : {"$max": "$created_at"},
        }},
        {"$sort": {"last_date": -1}},
        {"$limit": limit},
    ]
    urgency_map: dict = {}
    async for doc in logs_col().aggregate(pipeline):
        sid = doc["_id"]
        if sid:
            urgency_map[sid] = {
                "urgency_label": (doc.get("max_urgency") or "LOW").upper(),
                "date"         : _iso(doc.get("last_date")),
            }

    if urgency_map:
        conv_cursor = conv_col().find({"session_id": {"$in": list(urgency_map.keys())}})
        async for conv in conv_cursor:
            sid   = conv["session_id"]
            info  = urgency_map.get(sid, {})
            label = info.get("urgency_label", "LOW")
            result.append({
                "item_id"      : str(conv["_id"]),
                "date"         : info.get("date") or _iso(conv.get("updated_at")),
                "text"         : conv.get("title", ""),
                "urgency_label": label,
                "score"        : _URGENCY_SCORES.get(label, 1),
            })

    result.sort(key=lambda x: x.get("date") or "", reverse=True)
    return result[:limit]


@router.delete("/analysis-history/{item_id}", status_code=204)
async def delete_analysis_history_item(item_id: str):
    """Supprime un item par son _id MongoDB (identifiant unique universel)."""
    from bson import ObjectId
    from bson.errors import InvalidId
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="ID invalide")
    result = await logs_col().delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Élément non trouvé")


@router.get("/stats")
async def get_stats():
    """Statistiques agrégées pour le tableau de bord."""
    try:
        pipeline_urgency = [
            {"$unwind": "$messages"},
            {"$match": {"messages.urgency_label": {"$ne": None}}},
            {"$group": {
                "_id"  : "$messages.urgency_label",
                "count": {"$sum": 1},
            }},
        ]
        urgency_dist = {}
        async for doc in conv_col().aggregate(pipeline_urgency):
            urgency_dist[doc["_id"]] = doc["count"]

        total_convs = await conv_col().count_documents({})

        pipeline_last = [
            {"$sort": {"updated_at": -1}},
            {"$limit": 10},
            {"$project": {"_id": 0, "session_id": 1, "title": 1, "updated_at": 1,
                           "last_urgency": {"$arrayElemAt": [
                               "$messages.urgency_label", -1
                           ]}}},
        ]
        recent = []
        async for doc in conv_col().aggregate(pipeline_last):
            recent.append({
                "session_id"  : doc.get("session_id"),
                "title"       : doc.get("title"),
                "updated_at"  : _iso(doc.get("updated_at")),
                "last_urgency": doc.get("last_urgency"),
            })

        return {
            "total_conversations"  : total_convs,
            "urgency_distribution" : urgency_dist,
            "recent_conversations" : recent,
        }
    except Exception:
        return {
            "total_conversations"  : 0,
            "urgency_distribution" : {},
            "recent_conversations" : [],
            "note"                 : "Base de données non disponible.",
        }
