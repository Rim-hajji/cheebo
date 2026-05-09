import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import analyze, chat
from backend.api.routes import vets, conversations
from backend.database.mongo import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage : initialiser MongoDB
    try:
        await init_db()
        logger.info("MongoDB initialisé")
    except Exception as e:
        logger.warning(f"MongoDB non disponible : {e} — l'app fonctionne sans BD")
    yield
    # Arrêt : rien à faire (Motor gère la fermeture)


app = FastAPI(
    title="Cheebo Healthcare API",
    description="API vétérinaire IA — Cheebo. Aucun diagnostic médical.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(analyze.router,        prefix="/api/v1")
app.include_router(chat.router,           prefix="/api/v1")
app.include_router(vets.router,           prefix="/api/v1")
app.include_router(conversations.router,  prefix="/api/v1")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Cheebo Healthcare API v2.0 — MongoDB"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
