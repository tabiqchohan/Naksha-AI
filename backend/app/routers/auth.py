from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models.user_models import User, Base
from app.models.auth_schemas import UserCreate, UserResponse, Token, UserLogin
from app.auth.auth_utils import get_password_hash, verify_password, create_access_token
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

Base.metadata.create_all(bind=engine)


@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        credits=3,
        plan_type="free"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.post("/free-credits")
def claim_free_credits(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if current_user.credits >= 3:
        raise HTTPException(status_code=400, detail="Already have free credits")
    current_user.credits = 3
    db.commit()
    db.refresh(current_user)
    return {"message": "Free credits claimed!", "credits": current_user.credits}
