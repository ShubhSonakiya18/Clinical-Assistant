import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User, RefreshToken
from app.models.doctor import Doctor

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload["sub"]


def register_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    phone: str | None,
    clinic_name: str | None,
    specialization: str,
) -> tuple[User, Doctor]:
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
    )
    db.add(user)
    db.flush()

    doctor = Doctor(
        user_id=user.id,
        clinic_name=clinic_name,
        specialization=specialization,
    )
    db.add(doctor)
    db.commit()
    db.refresh(user)
    db.refresh(doctor)
    return user, doctor


def login_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def save_refresh_token(db: Session, user_id: uuid.UUID, token: str) -> None:
    rt = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.commit()


def rotate_refresh_token(db: Session, old_token: str) -> tuple[User, str] | None:
    token_hash = hash_token(old_token)
    rt = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow(),
    ).first()
    if not rt:
        return None
    rt.is_revoked = True
    db.flush()
    new_token = create_refresh_token()
    save_refresh_token(db, rt.user_id, new_token)
    user = db.query(User).filter(User.id == rt.user_id).first()
    return user, new_token


def revoke_refresh_token(db: Session, token: str) -> None:
    token_hash = hash_token(token)
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt:
        rt.is_revoked = True
        db.commit()
