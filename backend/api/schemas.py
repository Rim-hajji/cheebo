from pydantic import BaseModel
from typing import Dict, Any, Optional

class AnalyzeRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    results: Dict[str, Any]
    error: Optional[str] = None
