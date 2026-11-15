"""Single-origin deployment: API under /api and the built React application."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apps.api.main import app

application=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
application.mount('/api',app)
application.mount('/',StaticFiles(directory=Path(__file__).resolve().parents[1]/'web/dist',html=True))
