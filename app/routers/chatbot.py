from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/chatbot", tags=["AI Support Assistant"])

class ChatRequest(BaseModel):
    message: str

@router.post("/ask")
def query_chatbot(
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Directly queries the database for active session info, wallets, bookings, 
    and support tickets, while answering EV charging platform questions dynamically.
    """
    msg = req.message.lower()
    
    from app.core.database import engine
    from sqlmodel import Session, select
    from app.models.booking import Reservation
    from app.models.ticket import SupportTicket
    from app.models.station import Station
    
    # 1. Greet / Identity
    if any(k in msg for k in ["hello", "hi", "hey", "greetings"]):
        return {
            "reply": (
                f"Hello **{current_user.full_name or 'Driver'}**! ⚡ I am your GoBharat EV / Smart Charging AI Assistant.<br/><br/>"
                f"I am fully integrated with your driver profile, active support tickets, wallet registry, and routing networks. "
                f"Ask me about your wallet balance, route planning, solar renewable scores, or active support tickets!"
            )
        }
        
    # 2. Wallet Balance
    if any(k in msg for k in ["wallet", "balance", "money", "funds", "pay", "stripe"]):
        return {
            "reply": (
                f"💳 **Driver Wallet Status:**<br/>"
                f"• Active Balance: **₹{current_user.wallet_balance:.2f}**<br/>"
                f"• Registered Account: `{current_user.email}`<br/><br/>"
                f"You can deposit additional funds in increments of ₹250.00, ₹500.00, or ₹1000.00 via Stripe Sandbox on your Dashboard."
            )
        }

    # 3. Active Bookings / Reservations
    if any(k in msg for k in ["booking", "reservation", "reserve", "slot", "book"]):
        with Session(engine) as session:
            bookings = session.exec(select(Reservation).where(Reservation.user_id == current_user.id)).all()
            if bookings:
                reply = f"📅 **Your Active & Past Charger Bookings:**<br/>"
                # Sort bookings by created_at or just take latest 3
                sorted_bookings = sorted(bookings, key=lambda b: b.created_at or datetime.utcnow(), reverse=True)
                for b in sorted_bookings[:3]:
                    station = session.get(Station, b.station_id)
                    s_name = station.name if station else "Unknown Hub"
                    reply += f"• **{s_name}** | Port ID: `{str(b.port_id)[:8]}` | Status: **{b.status}** (Time: {b.start_time})<br/>"
                reply += "<br/>You can scan your secure encrypted check-in QR code directly inside the Wallet & Bookings page to initiate the power cycle!"
                return {"reply": reply}
            else:
                return {
                    "reply": "You do not have any active charger reservations. Select a battery pin on the Interactive Map and click 'Reserve Port' to secure a charging connector."
                }

    # 4. Support Tickets Status
    if any(k in msg for k in ["ticket", "support", "complaint", "issue", "resolve"]):
        with Session(engine) as session:
            tickets = session.exec(select(SupportTicket).where(SupportTicket.email == current_user.email)).all()
            if tickets:
                reply = f"🎫 **Your Support Tickets & Status:**<br/>"
                for t in tickets[:4]:
                    status_badge = "🟢 APPROVED / RESOLVED" if t.status == "RESOLVED" else "🔵 PENDING / OPEN"
                    reply += f"• **{t.subject}**: {status_badge} (Created: {t.created_at.strftime('%b %d, %H:%M')})<br/>"
                reply += "<br/>You can monitor this list in real-time in the Ticket registry at the bottom of the Support Hub."
                return {"reply": reply}
            else:
                return {
                    "reply": "You haven't submitted any support tickets. If you face any issues (e.g. connector faults or billing anomalies), submit a ticket on the Support Hub!"
                }

    # 5. Station Coordinates & Nagpur Density
    if any(k in msg for k in ["station", "location", "nagpur", "mumbai", "delhi", "bengaluru", "kolkata", "pune", "krishnagiri", "hyderabad", "jaipur"]):
        with Session(engine) as session:
            stations = session.exec(select(Station)).all()
            matched = []
            for s in stations:
                for keyword in ["nagpur", "mumbai", "delhi", "bengaluru", "bangalore", "kolkata", "pune", "krishnagiri", "hyderabad", "jaipur"]:
                    if keyword in msg and (keyword in s.name.lower() or keyword in s.address.lower() or (keyword == "bangalore" and "bengaluru" in s.address.lower())):
                        matched.append(s)
                        break
            if not matched and "station" in msg:
                matched = stations[:3]
                
            if matched:
                reply = f"📍 **GoBharat EV Charging Stations matching your query:**<br/>"
                for s in matched[:4]:
                    avail = sum(1 for p in s.ports if p.status == "AVAILABLE")
                    reply += f"• **{s.name}** ({s.address}) — **{avail}/{len(s.ports)} ports available**<br/>"
                return {"reply": reply}
            else:
                return {
                    "reply": "We couldn't find any stations matching that specific city keyword. However, GoBharat EV maps major highways including the Mumbai-Pune Expressway, Adyar central in Chennai, Connaught Place in Delhi, and Whitefield in Bangalore!"
                }

    # 6. Dynamic A* Routing & Emergency low-battery
    if any(k in msg for k in ["route", "dijkstra", "plan", "path", "elevation", "slope", "a*", "a star"]):
        return {
            "reply": (
                "🌐 **A* Topography-Aware Routing Engine:**<br/>"
                "• **Elevation Integration:** Our router gathers slope gradients along your route, factoring in power drainage on climbs and dynamic kinetic energy recapture (regen) on descents.<br/>"
                "• **Aerodynamic Drag:** Climate variables like headwind/tailwind speed, temperature, and wet precipitation friction are computed into your battery's consumption formula.<br/>"
                "• **Emergency Low-Battery Rerouting:** If your State-of-Charge (SoC) drops below **12%** at any segment, the solver automatically injects the nearest fast charger as a mandatory midpoint stop to eliminate range anxiety!"
            )
        }

    # 7. Regen Slip Limiter
    if any(k in msg for k in ["regen", "slip", "friction", "abs", "esp", "wet", "flooded"]):
        return {
            "reply": (
                "⚙️ **Regen & Slip Limiter Safety Protocol:**<br/>"
                "• **Dry Asphalt (μ = 0.85):** Normal operations, allowing up to 100% of regenerative energy recapture.<br/>"
                "• **Wet Asphalt (μ = 0.45):** The ABS/ESP slip limiter curtails kinetic energy recovery to **60%** to prevent rear-wheel lockup.<br/>"
                "• **Flooded Road (μ = 0.15):** Regenerative braking is heavily limited to **15%** of capacity to prevent aquaplaning and preserve steering stability.<br/>"
                "You can simulate road surface changes on the Map Portal sidebar and observe the live Regen Index calculations!"
            )
        }

    # 8. Connection Troubleshooting / 500 error / Supabase down
    if any(k in msg for k in ["error", "500", "database url", "connection", "fail", "broken", "offline", "api"]):
        return {
            "reply": (
                "🛠️ **Connection & Fallback Diagnostics:**<br/>"
                "If the live Supabase cluster connection encounters password validation errors, the platform automatically switches to a writable local SQLite database (`/tmp/ev_charging.db` in serverless cloud environments).<br/>"
                "This self-healing fallback ensures the backend stays online, tables are synced, and all 44 nationwide charging hubs load instantly!"
            )
        }

    # 9. List Website Features
    if any(k in msg for k in ["feature", "website", "consist", "what is this", "about"]):
        return {
            "reply": (
                "✨ **GoBharat EV Core Features Checklist:**<br/>"
                "1. **Interactive Leaflet Map Portal:** Dynamic dark/light maps displaying active charger networks.<br/>"
                "2. **A* Topography Solver:** Elevation-aware routing with SoC projection graphs.<br/>"
                "3. **Regen & Slip Limiter:** Road friction safety limiter simulation.<br/>"
                "4. **OCPP Telemetry Overrides:** Real-time port overrides on the Admin Fleet console.<br/>"
                "5. **Driver Wallet & Stripe Deposits:** Stripe sandbox cash deposits & slot booking ledger.<br/>"
                "6. **Support Hub & Tracking Registry:** File tickets, track resolution status, and get AI Diagnostics."
            )
        }

    # Default generic AI reply
    return {
        "reply": (
            "I am your GoBharat EV / Smart Charging Assistant. I can check your account's **wallet balance**, "
            "list your **bookings**, check your submitted **support tickets**, locate **charging stations** in cities like Nagpur, "
            "or explain the physics formulas behind our **A* elevation router** or **ABS slip limiter**. What can I help you with?"
        )
    }
