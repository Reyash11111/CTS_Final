from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .database import Base, engine
from .routers import auth, chat, dashboard, requests, review, validation
from .services import ml
from .routers.admin import router as admin_router

app = FastAPI(
    title="Prior Authorization Intelligence Platform",
    description=(
        "AI-assisted prior authorization automation with PDF extraction, "
        "medical necessity evaluation, ML scoring, reviewer routing, "
        "appeal prediction, contextual validation and audit trails."
    ),
    version="2.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in CORS_ORIGINS
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(requests.router)
app.include_router(review.router)
app.include_router(dashboard.router)
app.include_router(chat.router)
app.include_router(validation.router)
app.include_router(admin_router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)

    ready = ml.models_ready()

    print("\n==========================================")
    print(" PRIOR AUTHORIZATION PLATFORM")
    print("==========================================")
    print(
        "Policy-fit model:",
        "READY" if ready["policy_fit"] else "MISSING",
    )
    print(
        "Appeal model:",
        "READY" if ready["appeal_propensity"] else "MISSING",
    )

    if not all(ready.values()):
        print("\nWARNING: ML model files are missing.")

    print("==========================================\n")


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": "prior-authorization-platform",
        "models": ml.models_ready(),
    }
