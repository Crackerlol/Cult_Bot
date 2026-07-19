# database/models.py
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class Disciple(Base):
    __tablename__ = "disciples"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    nickname: Mapped[str] = mapped_column(String(64), nullable=True)
    can_change_nickname: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)  # ← новое

    finger_power: Mapped[float] = mapped_column(Float, default=0.0)
    rank: Mapped[str] = mapped_column(String(64), default="Новоприбывший")
    total_workouts: Mapped[int] = mapped_column(Integer, default=0)
    total_approaches: Mapped[int] = mapped_column(Integer, default=0)
    total_weight_lifted: Mapped[float] = mapped_column(Float, default=0.0)
    dasha_incidents_reported: Mapped[int] = mapped_column(Integer, default=0)
    semen_battles_won: Mapped[int] = mapped_column(Integer, default=0)
    semen_battles_lost: Mapped[int] = mapped_column(Integer, default=0)
    has_semen_debuff: Mapped[bool] = mapped_column(Boolean, default=False)
    semen_debuff_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    initiated_by_magister: Mapped[bool] = mapped_column(Boolean, default=False)
    initiation_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_training: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    trainings = relationship("Training", back_populates="disciple", cascade="all, delete-orphan")
    incidents = relationship("DashaIncident", back_populates="disciple", cascade="all, delete-orphan")

class Training(Base):
    __tablename__ = "trainings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciple_id: Mapped[int] = mapped_column(ForeignKey("disciples.id"), nullable=False)
    exercise: Mapped[str] = mapped_column(String(128), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    finger_power_earned: Mapped[float] = mapped_column(Float, nullable=False)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    disciple = relationship("Disciple", back_populates="trainings")

class DashaIncident(Base):
    __tablename__ = "dasha_incidents"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciple_id: Mapped[int] = mapped_column(ForeignKey("disciples.id"), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    threat_level: Mapped[int] = mapped_column(Integer, default=5)
    involved_semen: Mapped[bool] = mapped_column(Boolean, default=False)
    semen_defeated: Mapped[bool] = mapped_column(Boolean, default=False)
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    disciple = relationship("Disciple", back_populates="incidents")

class Ban(Base):
    __tablename__ = "bans"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciple_id: Mapped[int] = mapped_column(ForeignKey("disciples.id"), nullable=False)
    banned_by: Mapped[int] = mapped_column(Integer, nullable=False)  # telegram_id админа
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    banned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # связь не обязательна, но можно