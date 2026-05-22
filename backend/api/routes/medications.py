"""
Cheebo — Routes Pilulier (Medications)
CRUD complet + historique des traitements terminés, stockage MongoDB.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.database.mongo import get_db

router = APIRouter(tags=["medications"])


class MedicationPayload(BaseModel):
    id: str
    name: str
    dosage: str
    frequencyLabel: str
    intervalHours: int
    nextDose: str          # ISO-8601 string
    notes: Optional[str] = None
    isActive: bool = True
    notificationId: int
    petId: str = "default"


# ── Lecture ───────────────────────────────────────────────────────────

@router.get("/medications")
async def list_active(pet_id: str = "default"):
    """Retourne les traitements actifs/inactifs (non terminés)."""
    db = get_db()
    cursor = db["medications"].find(
        {"petId": pet_id, "status": {"$ne": "completed"}},
        {"_id": 0},
    ).sort("nextDose", 1)
    return [doc async for doc in cursor]


@router.get("/medications/history")
async def list_history(pet_id: str = "default"):
    """Retourne les traitements terminés, du plus récent au plus ancien."""
    db = get_db()
    cursor = db["medications"].find(
        {"petId": pet_id, "status": "completed"},
        {"_id": 0},
    ).sort("completedAt", -1)
    return [doc async for doc in cursor]


# ── Création ──────────────────────────────────────────────────────────

@router.post("/medications", status_code=201)
async def add_medication(payload: MedicationPayload):
    db = get_db()
    doc = {
        "id"            : payload.id,
        "petId"         : payload.petId,
        "name"          : payload.name,
        "dosage"        : payload.dosage,
        "frequencyLabel": payload.frequencyLabel,
        "intervalHours" : payload.intervalHours,
        "nextDose"      : payload.nextDose,
        "notes"         : payload.notes,
        "isActive"      : payload.isActive,
        "notificationId": payload.notificationId,
        "status"        : "active",
        "completedAt"   : None,
        "createdAt"     : datetime.now(timezone.utc).isoformat(),
    }
    await db["medications"].insert_one(doc)
    doc.pop("_id", None)
    return doc


# ── Modifications ─────────────────────────────────────────────────────

@router.put("/medications/{med_id}/toggle")
async def toggle_medication(med_id: str):
    """Bascule isActive et status (active ↔ inactive)."""
    db = get_db()
    med = await db["medications"].find_one(
        {"id": med_id, "status": {"$ne": "completed"}}, {"_id": 0}
    )
    if not med:
        raise HTTPException(404, "Médicament introuvable")
    new_active = not med["isActive"]
    new_status = "active" if new_active else "inactive"
    await db["medications"].update_one(
        {"id": med_id},
        {"$set": {"isActive": new_active, "status": new_status}},
    )
    med["isActive"] = new_active
    med["status"]   = new_status
    return med


@router.put("/medications/{med_id}/complete")
async def complete_medication(med_id: str):
    """Marque un traitement comme terminé — le déplace dans l'historique."""
    db = get_db()
    med = await db["medications"].find_one({"id": med_id}, {"_id": 0})
    if not med:
        raise HTTPException(404, "Médicament introuvable")
    completed_at = datetime.now(timezone.utc).isoformat()
    await db["medications"].update_one(
        {"id": med_id},
        {"$set": {"status": "completed", "isActive": False, "completedAt": completed_at}},
    )
    med["status"]      = "completed"
    med["isActive"]    = False
    med["completedAt"] = completed_at
    return med


# ── Suppression ───────────────────────────────────────────────────────

@router.delete("/medications/{med_id}", status_code=204)
async def delete_medication(med_id: str):
    db = get_db()
    result = await db["medications"].delete_one({"id": med_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Médicament introuvable")
