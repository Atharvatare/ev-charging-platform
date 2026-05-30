print("1. Importing standard libraries...", flush=True)
import os
import sys

print("2. Importing FastAPI & Uvicorn...", flush=True)
import fastapi
import uvicorn

print("3. Importing SQLModel...", flush=True)
import sqlmodel

print("4. Importing app.core.config...", flush=True)
from app.core import config

print("5. Importing app.core.database...", flush=True)
from app.core import database

print("6. Importing app.core.seed...", flush=True)
from app.core import seed

print("7. Importing app.ws.connection_manager...", flush=True)
from app.ws import connection_manager

print("8. Importing app.routers.auth...", flush=True)
from app.routers import auth

print("9. Importing app.routers.stations...", flush=True)
from app.routers import stations

print("10. Importing app.routers.routing...", flush=True)
from app.routers import routing

print("11. Importing app.routers.bookings...", flush=True)
from app.routers import bookings

print("12. Importing app.routers.wallet...", flush=True)
from app.routers import wallet

print("13. Importing app.routers.chatbot...", flush=True)
from app.routers import chatbot

print("All imports successfully resolved with zero blocks!", flush=True)
