import secrets
from datetime import datetime, timedelta
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from app.core.database import get_session
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.station import Port
from app.models.booking import Reservation, WalletTransaction
from app.ws.connection_manager import manager

router = APIRouter(prefix="/api/bookings", tags=["Charger Reservations"])

class ReserveRequest(BaseModel):
    port_id: UUID
    duration_hours: int = 1

@router.get("/active")
def list_active_reservations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all active charger reservations for the authenticated driver."""
    reservations = session.exec(
        select(Reservation)
        .where(Reservation.user_id == current_user.id, Reservation.status == "PENDING")
    ).all()

    active_bookings = []
    for res in reservations:
        port = session.get(Port, res.port_id)
        station = port.station if port else None
        
        active_bookings.append({
            "id": res.id,
            "port_id": res.port_id,
            "station_id": port.station_id if port else None,
            "station_name": station.name if station else "Unknown Station",
            "connector_type": port.connector_type if port else "Unknown",
            "power_kw": port.power_kw if port else 0.0,
            "start_time": res.start_time,
            "end_time": res.end_time,
            "qr_code": res.qr_code,
            "status": res.status
        })
        
    return active_bookings

@router.post("/reserve")
async def reserve_charger_port(
    req: ReserveRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Locks a specific charger port out for a driver. 
    Requires and charges a $2.00 reservation fee, updating port status and generating a secure QR token.
    """
    # 1. Fetch target Port
    port = session.get(Port, req.port_id)
    if not port:
        # Dynamically seed an OSM port and station on-the-fly to support global maps
        import uuid
        from app.models.station import Station
        
        station_id = uuid.uuid4()
        new_st = Station(
            id=station_id,
            name="Real-World OSM Charging Station",
            address="Dynamic OpenStreetMap Verified Location",
            latitude=19.0600,
            longitude=72.8600,
            rating=4.6
        )
        session.add(new_st)
        session.commit()
        
        port = Port(
            id=req.port_id,
            station_id=station_id,
            connector_type="CCS2 Fast Charger (OSM)",
            power_kw=150.0,
            price_per_kwh=18.5,
            status="AVAILABLE"
        )
        session.add(port)
        session.commit()
        session.refresh(port)
        
    if port.status != "AVAILABLE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"This port is currently {port.status} and cannot be reserved."
        )

    # 2. Check and charge wallet balance
    reserve_fee = 100.00
    if current_user.wallet_balance < reserve_fee:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Insufficient wallet balance. Lockout requires a ₹{reserve_fee:.2f} starting fee."
        )

    # Deduct funds and save transaction
    current_user.wallet_balance -= reserve_fee
    session.add(current_user)
    
    ledger = WalletTransaction(
        user_id=current_user.id,
        amount=-reserve_fee,
        transaction_type="CHARGE",
        description=f"Charger Reservation Lockout Fee - Port {port.connector_type}"
    )
    session.add(ledger)

    # 3. Create Reservation
    start = datetime.utcnow()
    end = start + timedelta(hours=req.duration_hours)
    qr_token = f"BHARAT_RES_{secrets.token_hex(4).upper()}_ACTIVE_{port.connector_type}"

    reservation = Reservation(
        user_id=current_user.id,
        port_id=port.id,
        start_time=start,
        end_time=end,
        status="PENDING",
        qr_code=qr_token
    )
    session.add(reservation)

    # 4. Lockout port status in DB
    port.status = "OCCUPIED"
    session.add(port)
    
    session.commit()
    session.refresh(reservation)

    # Real-time WebSocket broadcast to sync interactive map and operator grids
    await manager.broadcast({
        "type": "PORT_STATUS_UPDATE",
        "station_id": str(port.station_id),
        "port_id": str(port.id),
        "status": port.status
    })

    return {
        "message": "Charger port reserved successfully.",
        "reservation_id": reservation.id,
        "qr_code": qr_token,
        "new_balance": current_user.wallet_balance
    }

@router.post("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Cancels an active reservation, restores port status to AVAILABLE, and refunds the lockout fee."""
    res = session.get(Reservation, reservation_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation record not found.")

    if res.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if res.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending reservations can be cancelled.")

    # 1. Restore port status
    port = session.get(Port, res.port_id)
    if port:
        port.status = "AVAILABLE"
        session.add(port)

    # 2. Update Reservation status
    res.status = "CANCELLED"
    session.add(res)

    # 3. Refund wallet balance
    refund = 100.00
    current_user.wallet_balance += refund
    session.add(current_user)

    ledger = WalletTransaction(
        user_id=current_user.id,
        amount=refund,
        transaction_type="REFUND",
        description="Charger Reservation Cancellation Refund"
    )
    session.add(ledger)
    
    session.commit()
    
    if port:
        await manager.broadcast({
            "type": "PORT_STATUS_UPDATE",
            "station_id": str(port.station_id),
            "port_id": str(port.id),
            "status": port.status
        })
    
    return {"message": "Reservation cancelled successfully and fee refunded.", "new_balance": current_user.wallet_balance}

class SettleSessionRequest(BaseModel):
    cost: float

@router.post("/{reservation_id}/complete")
async def complete_charging_session(
    reservation_id: UUID,
    req: SettleSessionRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Completes a charging session, restores port status to AVAILABLE, and deducts the final cost from the database wallet."""
    res = session.get(Reservation, reservation_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation record not found.")

    if res.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    if res.status != "PENDING":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only active reservations can be completed.")

    # 1. Restore port status
    port = session.get(Port, res.port_id)
    if port:
        port.status = "AVAILABLE"
        session.add(port)

    # 2. Update Reservation status
    res.status = "COMPLETED"
    session.add(res)

    # 3. Deduct cost from wallet
    current_user.wallet_balance -= req.cost
    session.add(current_user)

    ledger = WalletTransaction(
        user_id=current_user.id,
        amount=-req.cost,
        transaction_type="CHARGE",
        description=f"OCPP Session Settle - {port.connector_type if port else 'EV Port'}"
    )
    session.add(ledger)
    
    session.commit()
    
    if port:
        await manager.broadcast({
            "type": "PORT_STATUS_UPDATE",
            "station_id": str(port.station_id),
            "port_id": str(port.id),
            "status": port.status
        })
    
    return {"message": "Session completed and settled persistently.", "new_balance": current_user.wallet_balance}

