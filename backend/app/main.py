from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.database import Base, engine
from app.rag.engine import get_rag_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(exist_ok=True)
    settings.knowledge_base_path.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    rag = get_rag_engine()
    if list(settings.knowledge_base_path.glob("**/*.pdf")) and rag.store.count() == 0:
        rag.ingest_knowledge_base()

    yield


app = FastAPI(
    title="UZAZI ASSISTANT API",
    description="Intelligent AI assistant for infertility and reproductive health inquiries with PDF knowledge base and Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://infertility-guide.vercel.app",
        "https://infertilityguide-production.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    rag = get_rag_engine()
    return {
        "status": "healthy",
        "gemini_configured": bool(settings.gemini_api_key),
        "knowledge_chunks": rag.store.count(),
    }
