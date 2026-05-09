"""
Cheebo — Routes /partner-vets
==============================
CRUD complet pour les vétérinaires partenaires stockés dans MongoDB.
"""

from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.mongo import partner_vets as vets_col

router = APIRouter()


# ── Schémas ──────────────────────────────────────────────────────────

class VetIn(BaseModel):
    name       : str
    phone      : str
    address    : Optional[str] = None
    specialties: List[str] = []
    available  : bool = True
    emergency  : bool = False


class VetOut(BaseModel):
    id         : str
    name       : str
    phone      : str
    address    : Optional[str] = None
    specialties: List[str] = []
    available  : bool
    emergency  : bool


def _fmt(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc.pop("created_at", None)
    return doc


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/partner-vets", response_model=List[VetOut])
async def list_vets(emergency_only: bool = False, available_only: bool = True):
    """Liste les vétérinaires partenaires. Filtre optionnel urgence / disponibilité."""
    query: dict = {}
    if available_only:
        query["available"] = True
    if emergency_only:
        query["emergency"] = True
    cursor = vets_col().find(query)
    return [_fmt(doc) async for doc in cursor]


@router.post("/partner-vets", response_model=VetOut, status_code=201)
async def create_vet(vet: VetIn):
    """Ajoute un nouveau vétérinaire partenaire."""
    doc = vet.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    result = await vets_col().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    doc.pop("created_at", None)
    return doc


@router.put("/partner-vets/{vet_id}", response_model=VetOut)
async def update_vet(vet_id: str, vet: VetIn):
    """Met à jour un vétérinaire partenaire."""
    try:
        oid = ObjectId(vet_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    result = await vets_col().find_one_and_update(
        {"_id": oid},
        {"$set": vet.model_dump()},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Vétérinaire non trouvé")
    return _fmt(result)


@router.delete("/partner-vets/{vet_id}", status_code=204)
async def delete_vet(vet_id: str):
    """Supprime un vétérinaire partenaire."""
    try:
        oid = ObjectId(vet_id)
    except Exception:
        raise HTTPException(status_code=400, detail="ID invalide")
    result = await vets_col().delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vétérinaire non trouvé")
