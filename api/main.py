"""KrishiRakshak AI — FastAPI Application."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import health, weather, crops, advisories, chat

app = FastAPI(
    title="KrishiRakshak AI API",
    description="Agricultural climate-resilience assistant backend for farmers in Maharashtra, India.",
    version="1.0.0",
)

# CORS configuration
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://krishi-rakshak-ai-two.vercel.app",
]
env_origins = os.getenv("ALLOWED_ORIGINS", "")
origins = list(default_origins)
if env_origins:
    for orig in env_origins.split(","):
        cleaned = orig.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers under /api prefix
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(weather.router, prefix="/api", tags=["Weather"])
app.include_router(crops.router, prefix="/api", tags=["Crops"])
app.include_router(advisories.router, prefix="/api", tags=["Advisories"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint providing service information."""
    return {
        "service": "KrishiRakshak AI API",
        "status": "online",
        "docs_url": "/docs",
    }
