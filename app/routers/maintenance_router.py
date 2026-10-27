from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Maintenance, Pitch, PitchStatus, MaintenanceStatus, User, UserRole
from app.schemas import MaintenanceCreate, MaintenanceUpdate, MaintenanceResponse
from app.auth import require_roles

router = APIRouter(prefix="/api/maintenances", tags=["Quản lý Bảo Trì Sân"])

@router.get("", response_model=List[MaintenanceResponse])
def get_all_maintenances(db: Session = Depends(get_db)):
    return db.query(Maintenance).order_by(Maintenance.created_at.desc()).all()

@router.post("", response_model=MaintenanceResponse)
def schedule_maintenance(
    maint_in: MaintenanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    pitch = db.query(Pitch).filter(Pitch.id == maint_in.pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Không tìm thấy sân thể thao")

    from datetime import datetime
    s_date = maint_in.start_date or (maint_in.start_time.split('T')[0] if maint_in.start_time else datetime.now().strftime("%Y-%m-%d"))
    e_date = maint_in.end_date or (maint_in.end_time.split('T')[0] if maint_in.end_time else datetime.now().strftime("%Y-%m-%d"))
    reason_text = maint_in.reason or maint_in.description or maint_in.title or "Bảo dưỡng sân định kỳ"
    status_val = MaintenanceStatus.SCHEDULED
    if maint_in.status:
        st_upper = str(maint_in.status).upper()
        if st_upper in ["DONE", "COMPLETED"]:
            status_val = MaintenanceStatus.DONE
        elif st_upper in ["IN_PROGRESS"]:
            status_val = MaintenanceStatus.IN_PROGRESS
        else:
            status_val = MaintenanceStatus.SCHEDULED

    new_maint = Maintenance(
        pitch_id=maint_in.pitch_id,
        start_date=s_date,
        end_date=e_date,
        reason=reason_text,
        cost=maint_in.cost or 0.0,
        status=status_val
    )
    pitch.status = PitchStatus.MAINTENANCE if status_val != MaintenanceStatus.DONE else PitchStatus.AVAILABLE
    db.add(new_maint)
    db.commit()
    db.refresh(new_maint)
    return new_maint

@router.put("/{maint_id}", response_model=MaintenanceResponse)
def update_maintenance(
    maint_id: int,
    maint_in: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    maint = db.query(Maintenance).filter(Maintenance.id == maint_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin bảo trì")

    if maint_in.pitch_id is not None:
        maint.pitch_id = maint_in.pitch_id
    if maint_in.start_date:
        maint.start_date = maint_in.start_date
    elif maint_in.start_time:
        maint.start_date = maint_in.start_time.split('T')[0]
    if maint_in.end_date:
        maint.end_date = maint_in.end_date
    elif maint_in.end_time:
        maint.end_date = maint_in.end_time.split('T')[0]
    if maint_in.reason:
        maint.reason = maint_in.reason
    elif maint_in.description or maint_in.title:
        maint.reason = maint_in.description or maint_in.title
    if maint_in.cost is not None:
        maint.cost = maint_in.cost
    if maint_in.status:
        st_upper = str(maint_in.status).upper()
        if st_upper in ["DONE", "COMPLETED"]:
            maint.status = MaintenanceStatus.DONE
            if maint.pitch:
                maint.pitch.status = PitchStatus.AVAILABLE
        elif st_upper in ["IN_PROGRESS"]:
            maint.status = MaintenanceStatus.IN_PROGRESS
            if maint.pitch:
                maint.pitch.status = PitchStatus.MAINTENANCE
        else:
            maint.status = MaintenanceStatus.SCHEDULED
            if maint.pitch:
                maint.pitch.status = PitchStatus.MAINTENANCE

    db.commit()
    db.refresh(maint)
    return maint

@router.post("/{maint_id}/complete", response_model=MaintenanceResponse)
def complete_maintenance(
    maint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    maint = db.query(Maintenance).filter(Maintenance.id == maint_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin bảo trì")

    maint.status = MaintenanceStatus.DONE
    if maint.pitch:
        maint.pitch.status = PitchStatus.AVAILABLE

    db.commit()
    db.refresh(maint)
    return maint

@router.delete("/{maint_id}")
def delete_maintenance(
    maint_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    maint = db.query(Maintenance).filter(Maintenance.id == maint_id).first()
    if not maint:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin bảo trì")

    if maint.pitch and maint.pitch.status == PitchStatus.MAINTENANCE:
        # Kiểm tra xem sân có đợt bảo trì nào khác đang chạy không
        other_active = db.query(Maintenance).filter(
            Maintenance.pitch_id == maint.pitch_id,
            Maintenance.id != maint.id,
            Maintenance.status != MaintenanceStatus.DONE
        ).first()
        if not other_active:
            maint.pitch.status = PitchStatus.AVAILABLE

    db.delete(maint)
    db.commit()
    return {"message": "Đã hủy đợt bảo trì thành công và cập nhật trạng thái sân"}


maintenance_alias = APIRouter(prefix="/api/maintenance", tags=["Quản lý Bảo Trì Sân"])

@maintenance_alias.get("", response_model=List[MaintenanceResponse])
def get_all_maintenances_alias(db: Session = Depends(get_db)):
    return get_all_maintenances(db=db)
