"""
DoctoAgent — WebSocket Chat Route
===================================
WebSocket /ws/chat — conversation temps réel (texte uniquement).
Images et vidéos continuent d'utiliser les routes HTTP existantes.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agents.groq_guard import groq_guard
from backend.agents.shared import orchestrator
from backend.database.redis_client import get_redis
from backend.api.routes.chat import (
    GREETING,
    ChatMessage,
    _SOCIAL_ONLY_MESSAGES,
    _acknowledgment_reply,
    _already_asked,
    _build_accumulated_context,
    _clean_agent_text,
    _follow_up_q,
    _get_partner_vets,
    _has_symptom_keywords,
    _info_already_in_message,
    _is_acknowledgment,
    _last_agent_was_question,
    _no_symptom_reply,
    _save_to_mongo,
)
from backend.nlp.pipeline import nlp_pipeline
from backend.api.routes.ws_notifications import notification_manager

logger = logging.getLogger(__name__)
router = APIRouter()


class _ConnectionManager:
    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    async def send(self, session_id: str, data: dict):
        ws = self._connections.get(session_id)
        if ws:
            try:
                await ws.send_text(json.dumps(data, ensure_ascii=False))
            except Exception:
                self._connections.pop(session_id, None)


manager = _ConnectionManager()


async def _update_conversation_title(session_id: str, language: str) -> None:
    """Background task — génère un titre Groq et l'enregistre dans MongoDB (une seule fois par session)."""
    try:
        r = await get_redis()
        title_flag = f"title_done:{session_id}"
        if await r.exists(title_flag):
            return
        await r.setex(title_flag, 7200, "1")

        raw_history = await r.lrange(f"conv:{session_id}", 0, 9)
        if not raw_history:
            return
        parts = []
        for item in raw_history:
            m = json.loads(item)
            role    = "Utilisateur" if m.get("role") == "user" else "Cheebo"
            content = m.get("content", "")[:120]
            parts.append(f"{role}: {content}")
        summary = " | ".join(parts)

        title = await groq_guard.generate_title(summary, language)
        if not title:
            return

        from backend.database.mongo import conversations as conv_col
        await conv_col().update_one(
            {"session_id": session_id},
            {"$set": {"title": title}},
        )
        logger.info(f"[WS {session_id[:8]}] Titre mis à jour : {title!r}")
    except Exception as exc:
        logger.warning(f"[WS {session_id[:8]}] _update_conversation_title échoué : {exc}")


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    session_id = str(uuid.uuid4())
    await manager.connect(session_id, websocket)
    logger.info(f"[WS] Connexion {session_id[:8]}")

    # Message de bienvenue immédiat
    await manager.send(session_id, {
        "type"      : "greeting",
        "session_id": session_id,
        "response"  : GREETING,
        "agent_type": "GREETING",
    })

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send(session_id, {
                    "type"   : "error",
                    "message": "Format JSON invalide.",
                })
                continue

            user_message = payload.get("message", "").strip()
            if not user_message:
                continue

            # ── Historique depuis Redis (Write-Through cache) ────────────
            redis_key = f"conv:{session_id}"
            history: List[ChatMessage] = []
            try:
                r = await get_redis()
                raw_history = await r.lrange(redis_key, 0, -1)
                for raw in raw_history:
                    m = json.loads(raw)
                    if "role" in m and "content" in m:
                        history.append(ChatMessage(
                            role       = m["role"],
                            content    = m["content"],
                            has_images = m.get("has_images", False),
                        ))
                # Sauvegarder le message utilisateur immédiatement
                await r.rpush(redis_key, json.dumps({"role": "user", "content": user_message, "has_images": False}))
                await r.expire(redis_key, 7200)
            except Exception as _redis_err:
                logger.warning(f"[WS {session_id[:8]}] Redis indisponible : {_redis_err} — historique vide")

            logger.info(f"[WS {session_id[:8]}] User: '{user_message[:60]}'")

            await manager.send(session_id, {
                "type"   : "status",
                "message": "Analyse en cours...",
            })

            try:
                analysis_text    = _build_accumulated_context(user_message, history)
                nlp_result       = nlp_pipeline.process(analysis_text)
                nlp_dict         = nlp_result if isinstance(nlp_result, dict) else (
                    nlp_result.model_dump() if hasattr(nlp_result, "model_dump") else vars(nlp_result)
                )
                entities         = nlp_dict.get("entities", [])
                intent           = nlp_dict.get("intent", "")
                urgency_from_nlp = nlp_dict.get("urgency_label", "LOW")
                language         = nlp_dict.get("language", "fr")

                has_symptom           = (
                    any(e.get("label") == "SYMPTOM" for e in entities)
                    or _has_symptom_keywords(analysis_text)
                    or urgency_from_nlp in ("MODERATE", "HIGH", "CRITICAL")
                )
                duree_detected        = any(e.get("label") == "DUREE" for e in entities)
                has_symptom_now       = _has_symptom_keywords(user_message)
                is_emergency          = intent == "emergency" or urgency_from_nlp in ("CRITICAL", "HIGH")
                is_answering_followup = _last_agent_was_question(history)
                has_medical_context   = has_symptom and any(m.role == "agent" for m in history)
                is_greeting_only      = user_message.strip().lower() in _SOCIAL_ONLY_MESSAGES
                is_ack                = _is_acknowledgment(user_message)

                go_to_pipeline = (
                    (is_emergency or has_symptom_now or is_answering_followup)
                    and not is_greeting_only
                    and not (is_ack and not has_symptom_now and not is_emergency)
                )

                # ── Pas de pipeline ────────────────────────────────────────
                if not go_to_pipeline:
                    if is_ack:
                        reply = await groq_guard.contextual_reply(user_message, language, history)
                        if not reply:
                            reply = _acknowledgment_reply(language)
                        asyncio.create_task(_save_to_mongo(
                            session_id, user_message, reply, "GREETING",
                            None, None, nlp_dict, {},
                        ))
                        try:
                            await r.rpush(redis_key, json.dumps({"role": "agent", "content": reply}))
                            await r.expire(redis_key, 7200)
                        except Exception:
                            pass
                        await manager.send(session_id, {
                            "type"      : "done",
                            "session_id": session_id,
                            "response"  : reply,
                            "agent_type": "GREETING",
                        })
                        continue

                    if has_medical_context:
                        reply = await groq_guard.contextual_reply(user_message, language, history)
                        if not reply:
                            reply = _no_symptom_reply(language, entities)
                        asyncio.create_task(_save_to_mongo(
                            session_id, user_message, reply, "QUESTION",
                            None, None, nlp_dict, {},
                        ))
                        try:
                            await r.rpush(redis_key, json.dumps({"role": "agent", "content": reply}))
                            await r.expire(redis_key, 7200)
                        except Exception:
                            pass
                        await manager.send(session_id, {
                            "type"      : "done",
                            "session_id": session_id,
                            "response"  : reply,
                            "agent_type": "QUESTION",
                        })
                        continue

                    reply = await groq_guard.fallback_response(
                        user_message=user_message,
                        language    =language,
                        entities    =entities,
                        history     =history,
                    )
                    if not reply:
                        reply = _no_symptom_reply(language, entities)
                    asyncio.create_task(_save_to_mongo(
                        session_id, user_message, reply, "QUESTION",
                        None, None, nlp_dict, {},
                    ))
                    try:
                        await r.rpush(redis_key, json.dumps({"role": "agent", "content": reply}))
                        await r.expire(redis_key, 7200)
                    except Exception:
                        pass
                    await manager.send(session_id, {
                        "type"      : "done",
                        "session_id": session_id,
                        "response"  : reply,
                        "agent_type": "QUESTION",
                    })
                    continue

                # ── Question animal avant pipeline ─────────────────────────
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
                        asyncio.create_task(_save_to_mongo(
                            session_id, user_message, reply, "QUESTION",
                            None, None, nlp_dict, {},
                        ))
                        try:
                            await r.rpush(redis_key, json.dumps({"role": "agent", "content": reply}))
                            await r.expire(redis_key, 7200)
                        except Exception:
                            pass
                        await manager.send(session_id, {
                            "type"      : "done",
                            "session_id": session_id,
                            "response"  : reply,
                            "agent_type": "QUESTION",
                        })
                        continue

                # ── Pipeline multi-agents ──────────────────────────────────
                await manager.send(session_id, {
                    "type"   : "status",
                    "message": "Consultation des agents IA...",
                })

                loop           = asyncio.get_running_loop()
                final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)
                level          = final_response.get("urgency", {}).get("level", "LOW")
                vets           = _get_partner_vets(level)

                async def _make_response(data: dict, msg: str, lvl: str) -> str:
                    agent_out = _clean_agent_text(data.get("synthesis", {}).get("response_text", ""))
                    if agent_out and len(agent_out) > 50:
                        return await groq_guard.quality_check(agent_out, msg, lvl)
                    return await groq_guard.generate_response(data, msg)

                # ── CRITICAL / HIGH ────────────────────────────────────────
                if level in ("CRITICAL", "HIGH"):
                    await manager.send(session_id, {
                        "type"   : "status",
                        "message": "Situation urgente détectée...",
                    })
                    chat_text = await _make_response(final_response, user_message, level)
                    asyncio.create_task(_save_to_mongo(
                        session_id, user_message, chat_text, "EMERGENCY",
                        level, vets, nlp_dict, final_response,
                    ))
                    asyncio.create_task(_update_conversation_title(session_id, language))
                    try:
                        await r.rpush(redis_key, json.dumps({"role": "agent", "content": chat_text}))
                        await r.expire(redis_key, 7200)
                    except Exception:
                        pass
                    done_msg = {
                        "type"         : "done",
                        "session_id"   : session_id,
                        "response"     : chat_text,
                        "agent_type"   : "EMERGENCY",
                        "urgency_label": level,
                        "partner_vets" : vets,
                    }
                    await manager.send(session_id, done_msg)
                    # Push alerte urgence vers tous les écrans de l'app
                    asyncio.create_task(notification_manager.broadcast({
                        "type"         : "emergency_alert",
                        "urgency_label": level,
                        "message"      : f"🚨 Urgence {level} détectée — consultez le chat Cheebo",
                        "partner_vets" : vets,
                    }))
                    continue

                # ── MODERATE ───────────────────────────────────────────────
                if level == "MODERATE":
                    sent_question = False
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
                            asyncio.create_task(_save_to_mongo(
                                session_id, user_message, reply, "QUESTION",
                                level, None, nlp_dict, final_response,
                            ))
                            try:
                                await r.rpush(redis_key, json.dumps({"role": "agent", "content": reply}))
                                await r.expire(redis_key, 7200)
                            except Exception:
                                pass
                            await manager.send(session_id, {
                                "type"         : "done",
                                "session_id"   : session_id,
                                "response"     : reply,
                                "agent_type"   : "QUESTION",
                                "urgency_label": level,
                            })
                            sent_question = True
                            break
                    if sent_question:
                        continue
                    chat_text = await _make_response(final_response, user_message, level)
                    asyncio.create_task(_save_to_mongo(
                        session_id, user_message, chat_text, "ANALYSIS",
                        level, vets, nlp_dict, final_response,
                    ))
                    asyncio.create_task(_update_conversation_title(session_id, language))
                    try:
                        await r.rpush(redis_key, json.dumps({"role": "agent", "content": chat_text}))
                        await r.expire(redis_key, 7200)
                    except Exception:
                        pass
                    await manager.send(session_id, {
                        "type"         : "done",
                        "session_id"   : session_id,
                        "response"     : chat_text,
                        "agent_type"   : "ANALYSIS",
                        "urgency_label": level,
                        "partner_vets" : vets,
                    })
                    continue

                # ── LOW ───────────────────────────────────────────────────
                chat_text = await _make_response(final_response, user_message, level)
                asyncio.create_task(_save_to_mongo(
                    session_id, user_message, chat_text, "ANALYSIS",
                    level, None, nlp_dict, final_response,
                ))
                asyncio.create_task(_update_conversation_title(session_id, language))
                try:
                    await r.rpush(redis_key, json.dumps({"role": "agent", "content": chat_text}))
                    await r.expire(redis_key, 7200)
                except Exception:
                    pass
                await manager.send(session_id, {
                    "type"         : "done",
                    "session_id"   : session_id,
                    "response"     : chat_text,
                    "agent_type"   : "ANALYSIS",
                    "urgency_label": level,
                })

            except Exception as e:
                logger.error(f"[WS {session_id[:8]}] Erreur : {e}", exc_info=True)
                await manager.send(session_id, {
                    "type"      : "error",
                    "response"  : "😔 Désolé, j'ai rencontré un problème technique. Pouvez-vous reformuler votre message ?",
                    "agent_type": "ERROR",
                })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"[WS] Déconnexion {session_id[:8]}")
    except Exception as e:
        manager.disconnect(session_id)
        logger.error(f"[WS] Erreur inattendue {session_id[:8]} : {e}", exc_info=True)
