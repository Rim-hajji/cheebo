"""
Cheebo — Routes /articles
==========================
Articles bien-être pour animaux de compagnie.
Stockés dans MongoDB, seedés au démarrage.
"""

from fastapi import APIRouter
from backend.database.mongo import get_db

router = APIRouter()


@router.get("/articles")
async def list_articles(category: str = "", species: str = ""):
    """Retourne les articles bien-être filtrés par catégorie ou espèce."""
    query: dict = {}
    if category:
        query["category"] = category
    if species:
        query["species"] = {"$in": [species, "tous"]}

    cursor = get_db()["articles"].find(query, {"_id": 0}).sort("order", 1)
    return [doc async for doc in cursor]


@router.get("/articles/daily")
async def daily_article():
    """Retourne un article aléatoire du jour pour la notification."""
    from datetime import date
    import hashlib
    seed = int(hashlib.md5(str(date.today()).encode()).hexdigest(), 16)
    total = await get_db()["articles"].count_documents({})
    if total == 0:
        return {}
    idx = seed % total
    cursor = get_db()["articles"].find({}, {"_id": 0}).sort("order", 1).skip(idx).limit(1)
    async for doc in cursor:
        return doc
    return {}
