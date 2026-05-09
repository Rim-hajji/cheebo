"""
DoctoAgent — Shared Orchestrator Singleton
==========================================
Instance unique de l'Orchestrateur partagée entre toutes les routes.
Python ne charge ce module qu'une seule fois (sys.modules cache),
donc l'Orchestrateur — et son SemanticRAGAgent (~470 MB) — n'est
instancié qu'une seule fois, peu importe combien de routes l'importent.
"""

import logging

from backend.agents.orchestrator import Orchestrator
from backend.nlp.pipeline import nlp_pipeline

logger = logging.getLogger("doctoagent.shared")

logger.info("Initialisation de l'orchestrateur partagé (singleton)...")
orchestrator = Orchestrator(kb_data=getattr(nlp_pipeline, "kb_data", {}))
logger.info("Orchestrateur partagé prêt.")
