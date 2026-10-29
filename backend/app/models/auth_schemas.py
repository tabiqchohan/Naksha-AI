from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: str
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    plan_type: str
    credits: int
    total_generations: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class TokenData(BaseModel):
    username: Optional[str] = None


class ProjectCreate(BaseModel):
    title: str
    plan_data: str
    plot_width: float
    plot_length: float
    building_type: str = "house"
    floors: int = 1


class ProjectResponse(BaseModel):
    id: int
    user_id: int
    title: str
    plot_width: float
    plot_length: float
    building_type: str
    floors: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PurchaseCredits(BaseModel):
    credits: int
    payment_method: str  # jazzcash, easypaisa, stripe


class PaymentResponse(BaseModel):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    payment_url: Optional[str] = None
