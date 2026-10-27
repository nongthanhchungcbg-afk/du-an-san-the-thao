from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Review, MatchPost, EventAnnouncement, User, UserRole, UserActivityLog
from app.schemas import (
    ReviewCreate, ReviewResponse,
    MatchPostCreate, MatchPostUpdate, MatchPostResponse,
    EventAnnouncementCreate, EventAnnouncementUpdate, EventAnnouncementResponse
)
from app.auth import get_current_user, get_current_active_user, require_roles

router = APIRouter(prefix="/api/community", tags=["Cộng Đồng, Giao Lưu & Đánh Giá"])

# 1. REVIEWS (ĐÁNH GIÁ)
@router.get("/reviews", response_model=List[ReviewResponse])
def get_reviews(db: Session = Depends(get_db)):
    return db.query(Review).order_by(Review.created_at.desc()).all()

@router.post("/reviews", response_model=ReviewResponse)
def create_review(review_in: ReviewCreate, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    user_id = current_user.id if current_user else None
    name = current_user.full_name if current_user else review_in.customer_name
    
    new_rev = Review(
        user_id=user_id,
        customer_name=name,
        rating=max(1, min(5, review_in.rating)),
        comment=review_in.comment,
        pitch_id=review_in.pitch_id
    )
    db.add(new_rev)
    db.commit()
    db.refresh(new_rev)
    return new_rev

@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    rev = db.query(Review).filter(Review.id == review_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá")
    
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and rev.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa đánh giá này")
        
    db.delete(rev)
    db.commit()
    return {"message": "Đã xóa đánh giá thành công"}

# 2. MATCH POSTS (ĐĂNG KÝ GIAO LƯU / TÌM KÈO)
@router.get("/matches", response_model=List[MatchPostResponse])
def get_match_posts(db: Session = Depends(get_db)):
    return db.query(MatchPost).order_by(MatchPost.created_at.desc()).all()

@router.post("/matches", response_model=MatchPostResponse)
def create_match_post(post_in: MatchPostCreate, db: Session = Depends(get_db), current_user: Optional[User] = Depends(get_current_user)):
    user_id = current_user.id if current_user else None
    name = current_user.full_name if (current_user and current_user.full_name) else post_in.author_name
    
    new_post = MatchPost(
        user_id=user_id,
        author_name=name,
        sport_type=post_in.sport_type,
        team_level=post_in.team_level,
        match_time=post_in.match_time,
        contact_phone=post_in.contact_phone,
        content=post_in.content
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.put("/matches/{post_id}", response_model=MatchPostResponse)
def update_match_post(
    post_id: int,
    post_in: MatchPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    post = db.query(MatchPost).filter(MatchPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng giao lưu")
    
    # QTV (Admin/Staff) hoặc chính tác giả có quyền sửa
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền sửa bài đăng này")
        
    update_data = post_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(post, key, value)
            
    db.commit()
    db.refresh(post)
    return post

@router.delete("/matches/{post_id}")
def delete_match_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    post = db.query(MatchPost).filter(MatchPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài đăng giao lưu")
    
    # QTV (Admin/Staff) hoặc chính tác giả có quyền xóa
    if current_user.role not in [UserRole.ADMIN, UserRole.STAFF] and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa bài đăng này")
        
    db.delete(post)
    db.commit()
    return {"message": "Đã xóa bài đăng giao lưu thành công"}

# 3. EVENT ANNOUNCEMENTS (HOẠT ĐỘNG & THÔNG BÁO SỰ KIỆN)
@router.get("/events", response_model=List[EventAnnouncementResponse])
def get_events(db: Session = Depends(get_db)):
    return db.query(EventAnnouncement).order_by(EventAnnouncement.created_at.desc()).all()

@router.post("/events", response_model=EventAnnouncementResponse)
def create_event(
    event_in: EventAnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    new_event = EventAnnouncement(
        title=event_in.title,
        category=event_in.category,
        description=event_in.description,
        event_date=event_in.event_date,
        banner_url=event_in.banner_url
    )
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@router.put("/events/{event_id}", response_model=EventAnnouncementResponse)
def update_event(
    event_id: int,
    event_in: EventAnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    event = db.query(EventAnnouncement).filter(EventAnnouncement.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
        
    update_data = event_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(event, key, value)
            
    db.commit()
    db.refresh(event)
    return event

@router.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.STAFF]))
):
    event = db.query(EventAnnouncement).filter(EventAnnouncement.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Không tìm thấy sự kiện")
        
    db.delete(event)
    db.commit()
    return {"message": "Đã xóa sự kiện thành công"}
