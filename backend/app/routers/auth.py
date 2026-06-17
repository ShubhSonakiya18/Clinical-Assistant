from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from jose import JWTError
from app.database import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, MeResponse, UserOut, DoctorOut,
)
from app.services import auth_service
from app.models.user import User
from app.models.doctor import Doctor

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth_header.split(" ", 1)[1]
    try:
        user_id = auth_service.decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_doctor(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Doctor:
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return doctor


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user, _ = auth_service.register_user(
        db, body.email, body.password, body.full_name,
        body.phone, body.clinic_name, body.specialization,
    )
    access_token = auth_service.create_access_token(str(user.id))
    refresh_token = auth_service.create_refresh_token()
    auth_service.save_refresh_token(db, user.id, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.login_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth_service.create_access_token(str(user.id))
    refresh_token = auth_service.create_refresh_token()
    auth_service.save_refresh_token(db, user.id, refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    result = auth_service.rotate_refresh_token(db, body.refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user, new_refresh = result
    return TokenResponse(
        access_token=auth_service.create_access_token(str(user.id)),
        refresh_token=new_refresh,
    )


@router.post("/logout", status_code=204)
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    auth_service.revoke_refresh_token(db, body.refresh_token)


@router.get("/me", response_model=MeResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    return MeResponse(
        user=UserOut.model_validate(user),
        doctor=DoctorOut.model_validate(doctor),
    )
