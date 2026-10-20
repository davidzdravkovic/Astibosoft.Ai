from contextlib import asynccontextmanager
import logging
import os

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException

from dto.ask import AskRequest, AskResponse, AskSource
from dto.embed import EmbedAcceptedResponse, EmbedRequest
from embedding.service import run_embed
from migrate.runner import apply_migrations
from rag.ask_service import (
    ASSISTANT_UNAVAILABLE_MESSAGE,
    AskServiceUnavailableError,
    RAG_SERVICE_UNAVAILABLE_CODE,
    prepare_ask,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _internal_key() -> str | None:
    value = os.getenv("RAG_INTERNAL_KEY")
    return value if value else None


def _require_internal_key(x_internal_key: str | None) -> None:
    expected = _internal_key()
    if expected and x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Invalid internal key")


@asynccontextmanager
async def lifespan(_: FastAPI):
    apply_migrations()
    logger.info(
        "LLM provider: gemini model=%s",
        os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    )

    if os.getenv("AI_EMBED_ON_START", "").strip().lower() in {"1", "true", "yes"}:
        logger.info("AI_EMBED_ON_START enabled — embedding knowledge corpus")
        run_embed(None)

    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/internal/embed", status_code=202, response_model=EmbedAcceptedResponse)
async def embed(
    request: EmbedRequest,
    background_tasks: BackgroundTasks,
    x_internal_key: str | None = Header(default=None),
) -> EmbedAcceptedResponse:
    _require_internal_key(x_internal_key)
    background_tasks.add_task(run_embed, request.sourceKey)
    return EmbedAcceptedResponse(sourceKey=request.sourceKey)


@app.post("/internal/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    x_internal_key: str | None = Header(default=None),
) -> AskResponse:
    _require_internal_key(x_internal_key)
    try:
        prepared = prepare_ask(request.question)
    except AskServiceUnavailableError:
        raise HTTPException(
            status_code=503,
            detail={
                "errorCode": RAG_SERVICE_UNAVAILABLE_CODE,
                "message": ASSISTANT_UNAVAILABLE_MESSAGE,
            },
        ) from None

    logger.info(
        "Ask retrieval chunks=%s contextChars=%s",
        len(prepared.chunks),
        len(prepared.context),
    )
    return AskResponse(
        answer=prepared.answer,
        sources=[
            AskSource(sourceKey=source.source_key, title=source.title)
            for source in prepared.sources
        ],
    )
