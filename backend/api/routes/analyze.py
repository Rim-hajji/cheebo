import asyncio
import logging
from fastapi import APIRouter, HTTPException
from backend.api.schemas import AnalyzeRequest
from backend.nlp.pipeline import nlp_pipeline
from backend.agents.shared import orchestrator

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
        # 1. Analyse NLP (synchrone — rapide, pas de blocage significatif)
        nlp_result = nlp_pipeline.process(request.text)

        # 2. Pipeline multi-agents dans un thread pool (évite de bloquer l'event loop async)
        loop = asyncio.get_event_loop()
        final_response = await loop.run_in_executor(None, orchestrator.handle, nlp_result)

        if final_response.get("status") == "error":
            raise HTTPException(status_code=500, detail=final_response.get("error", "Erreur interne"))

        return final_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur /analyze : {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erreur interne lors de l'analyse.")
