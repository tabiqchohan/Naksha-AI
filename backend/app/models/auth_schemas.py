from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


def _validate_password(value: str) -> str:
    if len(value or "") < 8:
        raise ValueError("Password must be at least 8 characters")
    return value


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _validate_password(value)

    @field_validator("username")
    @classmethod
    def check_username(cls, value: str) -> str:
        cleaned = (value or "").strip()
        if len(cleaned) < 3:
            raise ValueError("Username must be at least 3 characters")
        return cleaned


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    plan_type: str
    credits: int
    total_generations: int
    is_active: bool
    is_verified: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RegisterResponse(UserResponse):
    verification_token: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _validate_password(value)


class EmailVerificationConfirm(BaseModel):
    token: str


class MessageResponse(BaseModel):
    message: str
    token: Optional[str] = None


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
