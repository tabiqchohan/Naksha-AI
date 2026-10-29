from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_models import User
from app.auth.auth_utils import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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


def check_credits(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.plan_type.value == "pro" or current_user.plan_type.value == "enterprise":
        return current_user
    if current_user.credits <= 0:
        raise HTTPException(
            status_code=403,
            detail="Insufficient credits. Please upgrade to Pro or purchase more credits."
        )
    return current_user


def deduct_credit(user: User, db: Session):
    if user.plan_type.value == "free":
        user.credits -= 1
        user.total_generations += 1
        db.commit()
        db.refresh(user)
    return user
