from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Customer, Booking, UserRole
from app.schemas import CustomerCreate, CustomerUpdate, CustomerResponse
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/customers", tags=["Quản Lý Khách Hàng (Table 12 & Table 16)"])

@router.get("", response_model=List[CustomerResponse])
def get_customers(
    search: Optional[str] = Query(None, description="Tìm kiếm theo tên hoặc số điện thoại"),
    db: Session = Depends(get_db)
):
    query = db.query(Customer)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(or_(Customer.name.ilike(s), Customer.phone.ilike(s), Customer.email.ilike(s)))
    return query.order_by(Customer.created_at.desc()).all()

@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer_by_id(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại")
    return c

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(
    customer_in: CustomerCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Customer).filter(Customer.phone == customer_in.phone.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Số điện thoại {customer_in.phone} đã tồn tại trên hệ thống!")
    
    new_c = Customer(
        name=customer_in.name.strip(),
        phone=customer_in.phone.strip(),
        email=customer_in.email.strip() if customer_in.email else None,
        address=customer_in.address.strip() if customer_in.address else None
    )
    db.add(new_c)
    db.commit()
    db.refresh(new_c)
    return new_c

@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    customer_in: CustomerUpdate,
    db: Session = Depends(get_db)
):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại")
    
    if customer_in.phone and customer_in.phone.strip() != c.phone:
        existing = db.query(Customer).filter(Customer.phone == customer_in.phone.strip(), Customer.id != customer_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Số điện thoại này đã thuộc về khách hàng khác")
        c.phone = customer_in.phone.strip()

    if customer_in.name is not None:
        c.name = customer_in.name.strip()
    if customer_in.email is not None:
        c.email = customer_in.email.strip() if customer_in.email else None
    if customer_in.address is not None:
        c.address = customer_in.address.strip() if customer_in.address else None

    db.commit()
    db.refresh(c)
    return c

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db)
):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Khách hàng không tồn tại")
    db.delete(c)
    db.commit()
    return {"message": "Đã xóa khách hàng thành công", "id": customer_id}
