import os
from pathlib import Path

from dotenv import load_dotenv


# -----------------------------
# BASE DIRECTORY
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from backend/.env
load_dotenv(BASE_DIR / ".env")


# -----------------------------
# DATABASE
# -----------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'priorauth.db'}",
)


# -----------------------------
# JWT
# -----------------------------

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "change-me-in-production-please",
)

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_MINUTES = int(
    os.getenv("ACCESS_TOKEN_MINUTES", "720")
)


# -----------------------------
# FILE UPLOADS
# -----------------------------

UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        str(BASE_DIR / "uploads"),
    )
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# -----------------------------
# ML MODELS
# -----------------------------

MODELS_DIR = BASE_DIR / "ml" / "models"


# -----------------------------
# CORS
# -----------------------------

CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")


# -----------------------------
# MEDICAL NECESSITY
# -----------------------------

AUTO_APPROVE_MIN_POLICY_FIT = float(
    os.getenv(
        "AUTO_APPROVE_MIN_POLICY_FIT",
        "0.62",
    )
)

AUTO_DENY_MAX_POLICY_FIT = float(
    os.getenv(
        "AUTO_DENY_MAX_POLICY_FIT",
        "0.38",
    )
)

MIN_DOCUMENTATION_SCORE = float(
    os.getenv(
        "MIN_DOCUMENTATION_SCORE",
        "0.75",
    )
)


# -----------------------------
# GROQ / AI
# -----------------------------

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)