"""
Cheebo — WebSocket Notifications globales
==========================================
Canal push unique pour toute l'app :
  - Alertes urgence (CRITICAL/HIGH) relayées depuis ws_chat
  - Rappels médicaments (tâche de fond, vérification chaque minute)
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.database.mongo import get_db
from backend.database.redis_client import get_redis

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationManager:
    """Singleton — gère toutes les connexions WS de notification."""

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[client_id] = ws
        logger.info(f"[Notif] Client connecté {client_id[:8]} — {len(self._connections)} client(s)")

    def disconnect(self, client_id: str):
        self._connections.pop(client_id, None)

    async def broadcast(self, data: dict):
        """Envoie la notification à tous les clients connectés."""
        dead = []
        for cid, ws in list(self._connections.items()):
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                dead.append(cid)
        for cid in dead:
            self._connections.pop(cid, None)

    @property
    def has_clients(self) -> bool:
        return bool(self._connections)


# Singleton importé par ws_chat.py et main.py
notification_manager = NotificationManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    client_id = str(uuid.uuid4())
    await notification_manager.connect(client_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # canal push uniquement — on ignore les entrées
    except WebSocketDisconnect:
        notification_manager.disconnect(client_id)
    except Exception:
        notification_manager.disconnect(client_id)


async def medication_reminder_loop():
    """
    Tâche de fond : toutes les 60 s, cherche les médicaments actifs
    dont la prochaine dose est dans les 5 prochaines minutes et pousse
    un rappel WS. Déduplication via Redis (SETEX TTL 10 min) — survit aux redémarrages.
    """
    logger.info("[Notif] Boucle rappels médicaments démarrée")

    while True:
        await asyncio.sleep(60)
        if not notification_manager.has_clients:
            continue
        try:
            r     = await get_redis()
            db    = get_db()
            now   = datetime.now(timezone.utc)
            limit = now + timedelta(minutes=5)

            cursor = db["medications"].find(
                {"status": "active", "isActive": True},
                {"_id": 0},
            )
            async for med in cursor:
                raw = med.get("nextDose", "")
                if not raw:
                    continue
                try:
                    nd = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    if not nd.tzinfo:
                        nd = nd.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

                if not (now <= nd <= limit):
                    continue

                redis_key = f"notif_sent:{med['id']}_{nd.strftime('%Y-%m-%dT%H:%M')}"
                if await r.exists(redis_key):
                    continue
                await r.setex(redis_key, 600, "1")  # TTL 10 min

                mins = max(0, int((nd - now).total_seconds() / 60))
                await notification_manager.broadcast({
                    "type"        : "medication_reminder",
                    "med_id"      : med["id"],
                    "name"        : med["name"],
                    "dosage"      : med["dosage"],
                    "petId"       : med.get("petId", "default"),
                    "minutes_left": mins,
                    "message"     : f"💊 {med['name']} ({med['dosage']}) dans {mins} min",
                })
                logger.info(f"[Notif] Rappel médicament : {med['name']} dans {mins} min")

        except Exception as e:
            logger.error(f"[Notif] Erreur boucle : {e}", exc_info=True)
