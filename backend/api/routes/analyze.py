import asyncio
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from backend.api.schemas import AnalyzeRequest
from backend.nlp.pipeline import nlp_pipeline
from backend.agents.shared import orchestrator
from backend.database.mongo import analysis_logs

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze_symptom(request: AnalyzeRequest):
    """
    Point d'entrée principal.
    Reçoit un texte → pipeline NLP → orchestrateur multi-agents → réponse finale.
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Le texte fourni est vide.")

    logger.info(f"Requête /analyze : '{request.text[:60]}...'")

    try:
        nlp_result = nlp_pipeline.process(request.text)

        loop = asyncio.get_running_loop()
        final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)

        if final_response.get("status") == "error":
            raise HTTPException(status_code=500, detail=final_response.get("error", "Erreur interne"))

        # Persistance dans MongoDB
        urgency = final_response.get("urgency", {})
        try:
            await analysis_logs().insert_one({
                "item_id"      : uuid.uuid4().hex,
                "date"         : datetime.now(timezone.utc),
                "text"         : request.text,
                "urgency_label": urgency.get("level", "LOW"),
                "score"        : urgency.get("score", 0),
                "source"       : "analyze",
            })
        except Exception as db_err:
            logger.warning(f"Impossible de sauvegarder dans MongoDB : {db_err}")

        return final_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur /analyze : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'analyse.")
