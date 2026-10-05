from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.orm import Session

from .admin.routes import router as admin_router
from .auth.routes import router as auth_router
from .catalog.routes import router as catalog_router
from .demo import router as demo_router
from .farms.routes import router as farms_router
from .logistics.routes import router as logistics_router
from .orders.routes import router as orders_router
from .payments.routes import router as payments_router
from .trust.routes import router as trust_router
from .users.routes import router as users_router
from .shared.database import get_db

app = FastAPI(title="Farmer Marketplace API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()],
    allow_origin_regex=os.getenv("CORS_ORIGIN_REGEX", r"^http://192\.168\.\d{1,3}\.\d{1,3}:3000$"),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(farms_router)
app.include_router(catalog_router)
app.include_router(demo_router)
app.include_router(logistics_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(trust_router)
app.include_router(users_router)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


legacy_web = Path(__file__).resolve().parents[2] / "web"
if legacy_web.exists():
    app.mount("/", StaticFiles(directory=legacy_web, html=True), name="web")
