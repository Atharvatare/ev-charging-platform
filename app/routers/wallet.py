from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel
from app.core.database import get_session
from app.routers.auth import get_current_user
from app.models.user import User
from app.models.booking import WalletTransaction

router = APIRouter(prefix="/api/wallet", tags=["Wallet & Billing"])

class DepositRequest(BaseModel):
    amount: float

@router.get("/transactions", response_model=List[WalletTransaction])
def get_wallet_ledger(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all credit/debit transaction log records for the current user."""
    transactions = session.exec(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == current_user.id)
        .order_by(WalletTransaction.created_at.desc())
    ).all()
    return transactions

@router.post("/deposit")
def deposit_funds(
    req: DepositRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Executes a simulated Stripe payment deposit. Increments the user's wallet 
    balance and records an auditable credit ledger transaction.
    """
    if req.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than zero."
        )

    # 1. Update user balance in DB
    current_user.wallet_balance += req.amount
    session.add(current_user)
    
    # 2. Record ledger transaction
    transaction = WalletTransaction(
        user_id=current_user.id,
        amount=req.amount,
        transaction_type="DEPOSIT",
        description="Stripe Deposit - Wallet Top-up"
    )
    
    session.add(transaction)
    session.commit()
    session.refresh(current_user)
    
    return {
        "message": f"Successfully deposited ${req.amount:.2f} via Stripe Sandbox.",
        "new_balance": current_user.wallet_balance
    }
