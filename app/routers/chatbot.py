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
    Simulates an LLM-driven natural language virtual assistant that resolves 
    questions regarding EV charging, wallet balances, dynamic A* routing, and solar scores.
    """
    msg = req.message.lower()
    
    # Context-aware intelligent responses based on keyword queries
    if "hello" in msg or "hi" in msg:
        response = f"Hello {current_user.full_name or 'Driver'}! I am AURA, your AI Route Coordinator. How can I optimize your EV journey in San Francisco today?"
    
    elif "battery" in msg or "soc" in msg:
        response = (
            f"Your vehicle profile is set up as a standard Tesla Model 3 (75 kWh battery). "
            f"Currently, your wallet balance is ${current_user.wallet_balance:.2f}. "
            f"Our A* physics router will actively forecast your State of Charge (SoC) along any planned routes, factoring in aerodynamic drag and topographic slope gradients."
        )
        
    elif "route" in msg or "dijkstra" in msg or "plan" in msg:
        response = (
            "You can use our 'Interactive Map Portal' to plan topography-aware routes. "
            "Select a Departure and Destination node, adjust your start SoC, and click 'Solve Optimal Path'. "
            "If your battery drops below 12% at any node, our Emergency Low-Battery fallback system will automatically inject the nearest DC fast charger as an optimal stop!"
        )
        
    elif "solar" in msg or "green" in msg or "renewable" in msg:
        response = (
            "We track renewable energy scoring at all stations! "
            "For example, GreenGrid - Golden Gate Park has 100% solar self-sufficiency from its solar panels. "
            "Our routing edge weight formula gives eco-preference to stations with higher solar outputs."
        )
        
    elif "reserve" in msg or "book" in msg:
        response = (
            "To book a charger, click on any active battery station pin on our Map and choose 'Reserve Port'. "
            "This locks out the connector for your vehicle and generates an encrypted verification QR code inside your Dashboard to scan and initiate charging."
        )
        
    elif "wallet" in msg or "balance" in msg or "stripe" in msg:
        response = (
            f"Your active wallet balance is ${current_user.wallet_balance:.2f}. "
            f"You can deposit additional funds in increments of $25.00 via Stripe Sandbox directly inside the Wallet section on your Dashboard."
        )
        
    else:
        response = (
            "I am AURA EV, your AI route coordinator. I can help you compute optimal paths across San Francisco, "
            "verify active port reservations, analyze physical battery energy dissipation, or oversee solar output loads. What can I do for you?"
        )

    return {
        "reply": response
    }
