from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import urllib.parse

from app.database import get_db
from app.models import User, UserRole, WalletTransaction, WalletTransactionType, PaymentStatus, UserActivityLog
from app.schemas import WalletDepositRequest, WalletDepositResponse, WalletBalanceResponse, WalletTransactionResponse
from app.auth import get_current_active_user, require_roles

router = APIRouter(prefix="/api/wallet", tags=["Ví Điện Tử & Nạp Tiền"])

@router.get("/me", response_model=WalletBalanceResponse)
def get_my_wallet(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    txs = db.query(WalletTransaction).filter(WalletTransaction.user_id == current_user.id).order_by(WalletTransaction.created_at.desc()).all()
    return {
        "user_id": current_user.id,
        "wallet_balance": current_user.wallet_balance or 0.0,
        "full_name": current_user.full_name,
        "transactions": txs
    }

@router.post("/deposit-request", response_model=WalletDepositResponse)
def create_deposit_request(req: WalletDepositRequest, current_user: User = Depends(get_current_active_user)):
    if req.amount < 10000:
        raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 10,000 VNĐ")

    bank = req.bank_name or "MB"
    account_no = "0816227206"
    account_name = "TRAN THANH CHUNG"
    txn_code = f"NAPVI{current_user.id}{int(datetime.utcnow().timestamp()) % 100000}"
    transfer_content = f"NAPVI {current_user.id} {current_user.username}"

    # VietQR URL
    encoded_desc = urllib.parse.quote(transfer_content)
    encoded_name = urllib.parse.quote(account_name)
    qr_url = f"https://img.vietqr.io/image/{bank}-{account_no}-compact2.png?amount={int(req.amount)}&addInfo={encoded_desc}&accountName={encoded_name}"

    return {
        "transaction_code": txn_code,
        "amount": req.amount,
        "qr_url": qr_url,
        "bank_name": f"{bank} Bank",
        "account_number": account_no,
        "account_name": account_name,
        "transfer_content": transfer_content,
        "message": f"Vui lòng quét mã VietQR hoặc chuyển khoản {req.amount:,.0f} VNĐ với nội dung: '{transfer_content}'"
    }

@router.post("/confirm-deposit", response_model=WalletBalanceResponse)
def confirm_wallet_deposit(
    req: WalletDepositRequest, 
    request: Request,
    current_user: User = Depends(get_current_active_user), 
    db: Session = Depends(get_db)
):
    if req.amount < 10000:
        raise HTTPException(status_code=400, detail="Số tiền nạp tối thiểu là 10,000 VNĐ")

    current_user.wallet_balance = (current_user.wallet_balance or 0.0) + req.amount

    txn_code = f"NAP{int(datetime.utcnow().timestamp())}"
    tx = WalletTransaction(
        user_id=current_user.id,
        amount=req.amount,
        transaction_type=WalletTransactionType.DEPOSIT,
        payment_method="VIETQR",
        status=PaymentStatus.PAID,
        description=f"Nạp tiền vào ví qua VietQR ({req.bank_name or 'MB Bank'})",
        transaction_code=txn_code
    )
    db.add(tx)

    client_ip = request.client.host if request.client else "127.0.0.1"
    log = UserActivityLog(
        user_id=current_user.id,
        username=current_user.username,
        action=f"Nạp +{req.amount:,.0f} VNĐ vào ví điện tử (Số dư mới: {current_user.wallet_balance:,.0f} VNĐ)",
        role=current_user.role.value,
        ip_address=client_ip
    )
    db.add(log)
    db.commit()
    db.refresh(current_user)

    txs = db.query(WalletTransaction).filter(WalletTransaction.user_id == current_user.id).order_by(WalletTransaction.created_at.desc()).all()
    return {
        "user_id": current_user.id,
        "wallet_balance": current_user.wallet_balance,
        "full_name": current_user.full_name,
        "transactions": txs
    }
