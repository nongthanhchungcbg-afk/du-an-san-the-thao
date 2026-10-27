from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import Pitch, CourtType, PitchType, PitchStatus, UserRole, Maintenance, MaintenanceStatus
from app.schemas import PitchCreate, PitchUpdate, PitchResponse, CourtTypeCreate, CourtTypeUpdate, CourtTypeResponse
from app.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/pitches", tags=["Quản Lý Sân & Địa Điểm"])
courts_router = APIRouter(prefix="/api/courts", tags=["Quản Lý Sân (Chuẩn Table 16)"])
court_types_router = APIRouter(prefix="/api/court-types", tags=["Quản Lý Loại Sân (Chuẩn Table 16)"])

# ==========================================
# PITCH & COURT ENDPOINTS
# ==========================================
@router.get("", response_model=List[PitchResponse])
@courts_router.get("", response_model=List[PitchResponse])
def get_all_pitches(
    sport_type: Optional[PitchType] = None,
    status: Optional[PitchStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Pitch)
    if sport_type:
        query = query.filter(Pitch.sport_type == sport_type)
    if status:
        query = query.filter(Pitch.status == status)
    return query.order_by(Pitch.id.asc()).all()

@router.get("/{pitch_id}", response_model=PitchResponse)
@courts_router.get("/{pitch_id}", response_model=PitchResponse)
def get_pitch_by_id(pitch_id: int, db: Session = Depends(get_db)):
    pitch = db.query(Pitch).filter(Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Không tìm thấy sân thể thao")
    return pitch

@router.post("", response_model=PitchResponse)
@courts_router.post("", response_model=PitchResponse)
def create_pitch(
    pitch_in: PitchCreate,
    db: Session = Depends(get_db)
):
    new_pitch = Pitch(**pitch_in.model_dump())
    db.add(new_pitch)
    db.commit()
    db.refresh(new_pitch)

    # Tự động tạo lịch bảo trì nếu sân khởi tạo ở trạng thái MAINTENANCE
    if new_pitch.status == PitchStatus.MAINTENANCE:
        today_str = datetime.now().strftime("%Y-%m-%d")
        new_m = Maintenance(
            pitch_id=new_pitch.id,
            start_date=today_str,
            end_date=today_str,
            reason=f"Bảo trì cơ sở vật chất sân {new_pitch.name}",
            cost=0.0,
            status=MaintenanceStatus.IN_PROGRESS
        )
        db.add(new_m)
        db.commit()

    return new_pitch

@router.put("/{pitch_id}", response_model=PitchResponse)
@courts_router.put("/{pitch_id}", response_model=PitchResponse)
def update_pitch(
    pitch_id: int,
    pitch_in: PitchUpdate,
    db: Session = Depends(get_db)
):
    pitch = db.query(Pitch).filter(Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Không tìm thấy sân thể thao")
    
    old_status = pitch.status
    update_data = pitch_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(pitch, key, value)
    
    # Tự động đồng bộ với Lịch Bảo Trì (Table 13 & 14)
    if pitch.status == PitchStatus.MAINTENANCE:
        active_m = db.query(Maintenance).filter(
            Maintenance.pitch_id == pitch.id,
            Maintenance.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS])
        ).first()
        if not active_m:
            today_str = datetime.now().strftime("%Y-%m-%d")
            new_m = Maintenance(
                pitch_id=pitch.id,
                start_date=today_str,
                end_date=today_str,
                reason=f"Bảo trì thiết bị và mặt sân {pitch.name}",
                cost=0.0,
                status=MaintenanceStatus.IN_PROGRESS
            )
            db.add(new_m)
    elif pitch.status == PitchStatus.AVAILABLE and old_status == PitchStatus.MAINTENANCE:
        # Nếu chuyển từ MAINTENANCE sang AVAILABLE, hoàn tất các lịch bảo trì đang thực hiện
        db.query(Maintenance).filter(
            Maintenance.pitch_id == pitch.id,
            Maintenance.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.IN_PROGRESS])
        ).update({"status": MaintenanceStatus.DONE}, synchronize_session=False)

    db.commit()
    db.refresh(pitch)
    return pitch

@router.delete("/{pitch_id}")
@courts_router.delete("/{pitch_id}")
def delete_pitch(
    pitch_id: int,
    db: Session = Depends(get_db)
):
    pitch = db.query(Pitch).filter(Pitch.id == pitch_id).first()
    if not pitch:
        raise HTTPException(status_code=404, detail="Không tìm thấy sân thể thao")
    
    # Xóa các bản ghi bảo trì liên quan trước để tránh lỗi ràng buộc khóa ngoại
    db.query(Maintenance).filter(Maintenance.pitch_id == pitch_id).delete(synchronize_session=False)
    db.delete(pitch)
    db.commit()
    return {"message": "Đã xóa sân thể thao thành công", "id": pitch_id}

# ==========================================
# COURT TYPES ENDPOINTS (TABLE 9 & 16)
# ==========================================
@court_types_router.get("", response_model=List[CourtTypeResponse])
def get_court_types(db: Session = Depends(get_db)):
    types = db.query(CourtType).all()
    if not types:
        default_types = [
            CourtType(name="Bóng Đá Mini 5/7 Người", sport_type=PitchType.FOOTBALL, description="Sân cỏ nhân tạo tiêu chuẩn FIFA"),
            CourtType(name="Cầu Lông Thảm PVC", sport_type=PitchType.BADMINTON, description="Sân cầu lông sàn gỗ thảm chuyên nghiệp"),
            CourtType(name="Quần Vợt / Tennis", sport_type=PitchType.TENNIS, description="Sân tennis mặt cứng US Open"),
            CourtType(name="Phòng Gym & Thể Hình", sport_type=PitchType.GYM, description="Phòng tập máy móc hiện đại cao cấp"),
            CourtType(name="Sân Bóng Rổ Trong Nhà", sport_type=PitchType.BASKETBALL, description="Sân bóng rổ sàn gỗ cao cấp")
        ]
        db.add_all(default_types)
        db.commit()
        types = db.query(CourtType).all()
    return types

@court_types_router.post("", response_model=CourtTypeResponse)
def create_court_type(
    type_in: CourtTypeCreate,
    db: Session = Depends(get_db)
):
    new_type = CourtType(**type_in.model_dump())
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return new_type

@court_types_router.put("/{type_id}", response_model=CourtTypeResponse)
def update_court_type(
    type_id: int,
    type_in: CourtTypeUpdate,
    db: Session = Depends(get_db)
):
    ct = db.query(CourtType).filter(CourtType.id == type_id).first()
    if not ct:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại sân")
    for k, v in type_in.model_dump(exclude_unset=True).items():
        setattr(ct, k, v)
    db.commit()
    db.refresh(ct)
    return ct

@court_types_router.delete("/{type_id}")
def delete_court_type(type_id: int, db: Session = Depends(get_db)):
    ct = db.query(CourtType).filter(CourtType.id == type_id).first()
    if not ct:
        raise HTTPException(status_code=404, detail="Không tìm thấy loại sân")
    db.delete(ct)
    db.commit()
    return {"message": "Đã xóa loại sân thành công", "id": type_id}
