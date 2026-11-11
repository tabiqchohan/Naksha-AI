import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.auth_utils import (
    create_access_token,
    generate_token,
    get_password_hash,
    hash_token,
    token_matches,
    verify_password,
)
from app.auth.dependencies import get_current_active_user
from app.config import settings
from app.database import engine, get_db
from app.models.auth_schemas import (
    EmailVerificationConfirm,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterResponse,
    Token,
    UserCreate,
    UserResponse,
)
from app.models.user_models import Base, User
from app.services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["Authentication"])

Base.metadata.create_all(bind=engine)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _expired(value: datetime | None) -> bool:
    if value is None:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value < _now()


def _debug_tokens_enabled() -> bool:
    return (not settings.is_production) or os.getenv("AUTH_DEBUG_TOKENS", "false").lower() == "true"


def _link(kind: str, token: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/?{kind}={token}"


def _issue_verification(user: User) -> str:
    token = generate_token()
    user.verification_token_hash = hash_token(token)
    user.verification_token_expires = _now() + timedelta(hours=24)
    send_email(
        user.email,
        "Verify your NakshaAI email",
        f"Verify your email to secure your NakshaAI account:\n\n{_link('verify_token', token)}\n\nThis link expires in 24 hours.",
    )
    return token


def _issue_reset(user: User) -> str:
    token = generate_token()
    user.reset_token_hash = hash_token(token)
    user.reset_token_expires = _now() + timedelta(minutes=30)
    send_email(
        user.email,
        "Reset your NakshaAI password",
        f"Reset your NakshaAI password using this link:\n\n{_link('reset_token', token)}\n\nThis link expires in 30 minutes. Ignore this email if you did not request it.",
    )
    return token


@router.post("/register", response_model=RegisterResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    email = str(user.email).strip().lower()
    username = user.username.strip()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(func.lower(User.username) == username.lower()).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    db_user = User(
        email=email,
        username=username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        credits=3,
        plan_type="free",
    )
    db.add(db_user)
    db.flush()
    verification_token = _issue_verification(db_user)
    db.commit()
    db.refresh(db_user)

    payload = UserResponse.model_validate(db_user).model_dump()
    payload["verification_token"] = verification_token if _debug_tokens_enabled() else None
    return payload


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    identifier = form_data.username.strip()
    user = (
        db.query(User)
        .filter(or_(func.lower(User.username) == identifier.lower(), func.lower(User.email) == identifier.lower()))
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/password-reset/request", response_model=MessageResponse)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    token = None
    if user:
        token = _issue_reset(user)
        db.commit()
    return {
        "message": "If this email is registered, a password reset link has been sent.",
        "token": token if (user and _debug_tokens_enabled()) else None,
    }


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token_hash == hash_token(payload.token)).first()
    if not user or not token_matches(payload.token, user.reset_token_hash) or _expired(user.reset_token_expires):
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token")
    user.hashed_password = get_password_hash(payload.new_password)
    user.reset_token_hash = None
    user.reset_token_expires = None
    db.commit()
    return {"message": "Password updated successfully. Please sign in."}


@router.post("/email-verification/request", response_model=MessageResponse)
def request_email_verification(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.is_verified:
        return {"message": "Email is already verified."}
    token = _issue_verification(current_user)
    db.commit()
    return {
        "message": "Verification email sent." if token else "Verification email could not be sent. Configure SMTP.",
        "token": token if _debug_tokens_enabled() else None,
    }


@router.post("/email-verification/confirm", response_model=MessageResponse)
def confirm_email_verification(payload: EmailVerificationConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token_hash == hash_token(payload.token)).first()
    if not user or not token_matches(payload.token, user.verification_token_hash) or _expired(user.verification_token_expires):
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires = None
    db.commit()
    return {"message": "Email verified successfully."}


@router.post("/free-credits")
def claim_free_credits(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.credits >= 3:
        raise HTTPException(status_code=400, detail="Already have free credits")
    current_user.credits = 3
    db.commit()
    db.refresh(current_user)
    return {"message": "Free credits claimed!", "credits": current_user.credits}
