import os
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, Session

from app.core.config import settings
from app.core.database import init_db
from app.core.seed import seed_database
from app.ws.connection_manager import manager

# Import routers
from app.routers import auth, stations, routing, bookings, wallet, chatbot

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Futuristic AI-powered EV Route Coordinator & Charging Station Locator Platform API",
    version="1.0.0"
)

# Enable CORS for cross-origin client dashboard integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directories if they do not exist
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up templates engine
templates = Jinja2Templates(directory="app/templates")

# Register Micro-routers
app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(routing.router)
app.include_router(bookings.router)
app.include_router(wallet.router)
app.include_router(chatbot.router)

# -------------------------------------------------------------
# DATABASE INIT & SEEDING ON STARTUP
# -------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """Triggers PostgreSQL schema build and spatial coordinates seeding."""
    print("--------------------------------------------------")
    print("BOOTING GOVOLT EV DATABASE ENGINE...")
    try:
        init_db()
        print("DATABASE INIT SUCCESS: PostGIS Loaded, Tables Synced!")
        
        print("SEEDING TELEMETRY STATIONS GRID...")
        seed_database()
        print("DATABASE SEED SUCCESS: SF Stations Seeding complete!")
    except Exception as e:
        print(f"DATABASE STARTUP FAULT: {e}")
        print("Proceeding with API runtime stubs...")
    print("--------------------------------------------------")

# -------------------------------------------------------------
# JINJA2 FRONTEND VIEW ROUTES
# -------------------------------------------------------------
@app.get("/")
def get_landing_page(request: Request):
    """Serves the animated futuristic landing hero view."""
    return templates.TemplateResponse(request, "landing.html", {"request": request})

@app.get("/portal")
def get_map_portal_page(request: Request):
    """Serves the full-width CartoDB Dark Matter map planner portal."""
    return templates.TemplateResponse(request, "portal.html", {"request": request})

@app.get("/dashboard")
def get_user_dashboard_page(request: Request):
    """Serves the wallet billing deposits and bookings dashboard."""
    return templates.TemplateResponse(request, "dashboard.html", {"request": request})

@app.get("/admin")
def get_admin_dashboard_page(request: Request):
    """Serves the admin socket health monitoring control grid."""
    return templates.TemplateResponse(request, "admin.html", {"request": request})

# -------------------------------------------------------------
# WEBSOCKET REAL-TIME STREAMING
# -------------------------------------------------------------
@app.websocket("/ws")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    """
    Handles active WebSocket clients, listening for client heartbeat logs 
    and streaming live charger state changes to map HUD overlays.
    """
    await manager.connect(websocket)
    try:
        # Initial greeting broadcast
        await websocket.send_json({
            "type": "SYSTEM",
            "message": "Connected to goVolt EV Telemetry Stream."
        })
        
        while True:
            # Keep connection alive, listen for client socket payloads (e.g. simulated OCPP scans)
            data = await websocket.receive_text()
            print(f"WS Telemetry Received from client: {data}")
            
            # Echo telemetry logs back or broadcast event
            await manager.broadcast({
                "type": "TELEMETRY_LOG",
                "message": f"Broadcast telemetry event logged: {data}"
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
