"""
Cheebo — Routes /partner-vets
==============================
CRUD complet pour les vétérinaires partenaires stockés dans MongoDB.
Inclut /vets/nearby?lat=X&lng=Y — tri par distance GPS (Haversine).
"""

import math
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.database.mongo import partner_vets as vets_col


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance en km entre deux coordonnées GPS (formule de Haversine)."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(d_lng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))

router = APIRouter()


# ── Schémas ──────────────────────────────────────────────────────────

class VetIn(BaseModel):
    name       : str
    phone      : str
    address    : Optional[str] = None
    specialties: List[str] = []
    available  : bool = True
    emergency  : bool = False
    lat        : Optional[float] = None
    lng        : Optional[float] = None


class VetOut(BaseModel):
    id         : str
    name       : str
    phone      : str
    address    : Optional[str] = None
    specialties: List[str] = []
    available  : bool
    emergency  : bool
    lat        : Optional[float] = None
    lng        : Optional[float] = None


def _fmt(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    doc.pop("created_at", None)
    # Garantir que lat/lng sont présents (None si absents)
    doc.setdefault("lat", None)
    doc.setdefault("lng", None)
    return doc


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/vets/nearby")
async def nearby_vets(
    lat       : float = Query(..., description="Latitude GPS de l'utilisateur"),
    lng       : float = Query(..., description="Longitude GPS de l'utilisateur"),
    radius_km : float = Query(100, description="Rayon de recherche en km"),
    limit     : int   = Query(5,   description="Nombre max de résultats"),
):
    """
    Retourne les vétérinaires disponibles triés par distance GPS.
    Si aucun vet n'est dans le rayon, retourne les `limit` plus proches quand même.
    """
    cursor = vets_col().find(
        {"available": True, "lat": {"$exists": True, "$ne": None}},
        {"_id": 0},
    )
    results = []
    async for doc in cursor:
        v_lat = doc.get("lat")
        v_lng = doc.get("lng")
        if v_lat is None or v_lng is None:
            continue
        dist = _haversine(lat, lng, v_lat, v_lng)
        doc["distance_km"] = round(dist, 1)
        results.append(doc)

    results.sort(key=lambda x: x["distance_km"])

    # Si aucun vet dans le rayon → retourner les plus proches quand même
    in_radius = [v for v in results if v["distance_km"] <= radius_km]
    return (in_radius if in_radius else results)[:limit]


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
