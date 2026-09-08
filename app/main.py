"""FastAPI application entrypoint for Tasks 1-6."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy import text
from app.core.config import settings
from app.database.session import engine
from app.routers import auth
from app.routers.forms import forms_router, fields_router, public_router
from app.routers.files import router as files_router

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database connection successful.")
    except Exception as exc:
        print("Database connection failed:", exc)
        raise
    yield

app=FastAPI(title=settings.app_name,lifespan=lifespan)
app.include_router(auth.router)
app.include_router(forms_router)
app.include_router(fields_router)
app.include_router(public_router)
app.include_router(files_router)

@app.get("/")
def root():
    return FileResponse(FRONTEND/"index.html")

@app.get("/form/{slug}")
def public_form_page(slug:str):
    return FileResponse(FRONTEND/"index.html")

@app.get("/health")
def health_check():
    return {"status":"ok"}

@app.get("/{asset_path:path}")
def frontend_assets(asset_path:str):
    path=FRONTEND/asset_path
    if path.is_file():
        return FileResponse(path)
    return FileResponse(FRONTEND/"index.html")
