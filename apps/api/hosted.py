"""Single-origin deployment: API under /api and the built React application."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apps.api.main import app
from apps.api.publication import article

application=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
application.mount('/api',app)
application.add_api_route('/writeup',article,methods=['GET'],include_in_schema=False)
application.mount('/',StaticFiles(directory=Path(__file__).resolve().parents[1]/'web/dist',html=True))
