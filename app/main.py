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
    description="Futuristic AI-powered GoBharat EV Route Coordinator & Charging Station Locator Platform API",
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

# Create static directories if they do not exist (safely caught for Vercel's read-only runtime)
try:
    os.makedirs("app/static/css", exist_ok=True)
    os.makedirs("app/static/js", exist_ok=True)
except OSError:
    pass

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
    """Triggers PostgreSQL schema build and spatial coordinates seeding with environment audits synchronously."""
    print("--------------------------------------------------")
    print("BOOTING GOBHARAT EV DATABASE ENGINE...")
    
    # Secure API Keys Audit
    secret = os.getenv("SECRET_KEY")
    if not secret or secret == "7d4b4a11f26a11394c8b2d41b8a5d3c8c24f6ae9bcfd9f4e244fe7ad54b51815":
        print("[WARNING] SECURITY: Using default or empty SECRET_KEY. Configure a strong SECRET_KEY in environment variable!")
    else:
        print("[OK] Security Check: Backend SECRET_KEY configured securely.")
        
    try:
        print("Starting database init & seeding...")
        init_db()
        print("DATABASE INIT SUCCESS: Tables Synced!")
        seed_database()
        print("DATABASE SEED SUCCESS: Seeding complete!")
    except Exception as e:
        print(f"DATABASE STARTUP FAULT: {e}")
            
    print("FastAPI ready to handle requests.")
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

@app.get("/about")
def get_about_and_support_page(request: Request):
    """Serves the stunning corporate About Company Profile."""
    return templates.TemplateResponse(request, "about.html", {"request": request})

@app.get("/support")
def get_support_hub_page(request: Request):
    """Serves the driver help and corporate support ticketing center."""
    return templates.TemplateResponse(request, "support.html", {"request": request})

@app.get("/login")
def get_login_and_register_page(request: Request):
    """Serves the stunning corporate and driver login and registration page."""
    return templates.TemplateResponse(request, "login.html", {"request": request})

# In-memory corporate support ticketing ledger
SUPPORT_TICKETS = []

from pydantic import BaseModel
class ContactRequest(BaseModel):
    name: str
    email: str
    subject: str
    message: str

@app.post("/api/contact/submit")
def submit_contact_ticket(req: ContactRequest):
    """Saves a driver support ticket persistently in the database."""
    from fastapi import HTTPException
    from sqlmodel import Session
    from app.core.database import engine
    from app.models.ticket import SupportTicket
    
    if not req.name or not req.email or not req.subject or not req.message:
        raise HTTPException(status_code=400, detail="All contact form fields are required.")
    
    with Session(engine) as session:
        ticket = SupportTicket(
            name=req.name,
            email=req.email,
            subject=req.subject,
            message=req.message,
            status="OPEN"
        )
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        ticket_id = str(ticket.id)
        
    print(f"[OK] Database support ticket logged: {ticket_id} from {req.email} regarding '{req.subject}'")
    return {
        "message": "Support ticket submitted successfully. GoBharat EV team will contact you shortly.",
        "ticket_id": ticket_id
    }

@app.get("/api/contact/tickets")
def get_all_support_tickets():
    """Retrieves all driver support tickets from the database."""
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.ticket import SupportTicket
    
    with Session(engine) as session:
        tickets = session.exec(select(SupportTicket)).all()
        # Sort in-memory desc by created_at since it's mock
        tickets.sort(key=lambda t: t.created_at or datetime.utcnow(), reverse=True)
        return tickets

@app.patch("/api/contact/tickets/{ticket_id}/status")
def update_support_ticket_status(ticket_id: str, status: str):
    """Updates status ('OPEN' or 'RESOLVED') of a support ticket."""
    from fastapi import HTTPException
    from sqlmodel import Session
    from uuid import UUID
    from app.core.database import engine
    from app.models.ticket import SupportTicket
    
    try:
        ticket_uuid = UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket UUID format.")
        
    with Session(engine) as session:
        ticket = session.get(SupportTicket, ticket_uuid)
        if not ticket:
            raise HTTPException(status_code=404, detail="Support ticket not found.")
        ticket.status = status
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket

@app.delete("/api/contact/tickets/{ticket_id}")
def delete_support_ticket(ticket_id: str):
    """Deletes a support ticket permanently from the database."""
    from fastapi import HTTPException
    from sqlmodel import Session
    from uuid import UUID
    from app.core.database import engine
    from app.models.ticket import SupportTicket
    
    try:
        ticket_uuid = UUID(ticket_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ticket UUID format.")
        
    with Session(engine) as session:
        ticket = session.get(SupportTicket, ticket_uuid)
        if not ticket:
            raise HTTPException(status_code=404, detail="Support ticket not found.")
        session.delete(ticket)
        session.commit()
        return {"message": "Support ticket deleted successfully."}

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
            "message": "Connected to GoBharat EV Telemetry Stream."
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
