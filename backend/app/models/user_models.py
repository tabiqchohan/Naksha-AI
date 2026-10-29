from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class PlanType(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    plan_type = Column(Enum(PlanType), default=PlanType.FREE)
    credits = Column(Integer, default=3)
    total_generations = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    plan_data = Column(String, nullable=True)  # JSON as string
    plot_width = Column(Float)
    plot_length = Column(Float)
    building_type = Column(String, default="house")
    floors = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    amount_pkr = Column(Float, nullable=False)
    amount_usd = Column(Float)
    credits_purchased = Column(Integer, nullable=False)
    payment_method = Column(String)  # jazzcash, easypaisa, stripe
    transaction_id = Column(String, unique=True)
    status = Column(String, default="pending")  # pending, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
