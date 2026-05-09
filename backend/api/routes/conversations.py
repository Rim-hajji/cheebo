"""
Cheebo — Routes /conversations
================================
Historique des conversations stocké dans MongoDB.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.mongo import conversations as conv_col

router = APIRouter()


class MessageOut(BaseModel):
    role         : str
    content      : str
    agent_type   : Optional[str] = None
    urgency_label: Optional[str] = None
    timestamp    : Optional[str] = None


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
