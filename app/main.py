"""FastAPI Application Entrypoint for RAG + MCP Capstone Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.router import api_router


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=(
            "Multi-Context Intelligent RAG System: Self-Improving, Agentic Platform "
            "for Advanced Customer Support leveraging Hybrid Retrieval, MCP Context "
            "Merging, Remote Colab LLM inference, and Explainable AI."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Cross-Origin Resource Sharing (CORS) Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API Endpoints under /api/v1 prefix
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Root-level canonical route shortcuts
    from app.api.endpoints import health, rag, documents, knowledge_base
    app.include_router(health.router)
    app.include_router(rag.router)
    app.include_router(documents.router)
    app.include_router(knowledge_base.router)

    @app.get("/", tags=["Root"])
    async def root():
        """Welcome route pointing to interactive documentation."""
        return {
            "message": "Welcome to the Multi-Context Intelligent RAG + MCP Customer Support API",
            "version": settings.VERSION,
            "docs": "/docs",
            "health": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.APP_HOST}:{settings.APP_PORT}...")
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=settings.DEBUG)
