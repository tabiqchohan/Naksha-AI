from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_models import User, plan_value
from app.auth.auth_utils import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_optional_user(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        username = verify_token(token, HTTPException(status_code=401, detail="Invalid token"))
        user = db.query(User).filter(User.username == username).first()
        return user if user and user.is_active else None
    except Exception:
        return None


def check_credits(current_user: User = Depends(get_current_active_user)):
    if plan_value(current_user.plan_type) in ["pro", "enterprise"]:
        return current_user
    if (current_user.credits or 0) <= 0:
        raise HTTPException(
            status_code=403,
            detail="Insufficient credits. Please upgrade to Pro or purchase more credits.",
        )
    return current_user


def deduct_credit(user: User, db: Session):
    if plan_value(user.plan_type) == "free":
        user.credits = max(0, (user.credits or 0) - 1)
        user.total_generations = (user.total_generations or 0) + 1
        db.commit()
        db.refresh(user)
    return user
