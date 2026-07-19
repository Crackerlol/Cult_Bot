# database/models.py

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class Disciple(Base):
    """Ученик Магистра Естествознания."""
    __tablename__ = "disciples"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Сила указательного пальца (опыт)
    finger_power: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Ранг ученика
    rank: Mapped[str] = mapped_column(String(64), default="Новоприбывший")
    
    # Статистика тренировок
    total_workouts: Mapped[int] = mapped_column(Integer, default=0)
    total_approaches: Mapped[int] = mapped_column(Integer, default=0)
    total_weight_lifted: Mapped[float] = mapped_column(Float, default=0.0)  # в килограммах
    
    # Борьба с Дашкой
    dasha_incidents_reported: Mapped[int] = mapped_column(Integer, default=0)
    semen_battles_won: Mapped[int] = mapped_column(Integer, default=0)
    semen_battles_lost: Mapped[int] = mapped_column(Integer, default=0)
    
    # Дебаффы
    has_semen_debuff: Mapped[bool] = mapped_column(Boolean, default=False)
    semen_debuff_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Посвящение
    initiated_by_magister: Mapped[bool] = mapped_column(Boolean, default=False)
    initiation_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Даты
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_training: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Связь с тренировками
    trainings: Mapped[list["Training"]] = relationship(back_populates="disciple", cascade="all, delete-orphan")
    incidents: Mapped[list["DashaIncident"]] = relationship(back_populates="disciple", cascade="all, delete-orphan")


class Training(Base):
    """Запись о тренировке ученика."""
    __tablename__ = "trainings"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciple_id: Mapped[int] = mapped_column(ForeignKey("disciples.id"), nullable=False)
    
    # Параметры тренировки
    exercise: Mapped[str] = mapped_column(String(128), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Начисленная сила пальца
    finger_power_earned: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Дата
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь
    disciple: Mapped["Disciple"] = relationship(back_populates="trainings")


class DashaIncident(Base):
    """Инцидент с Дашкой или её прихвостнями."""
    __tablename__ = "dasha_incidents"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    disciple_id: Mapped[int] = mapped_column(ForeignKey("disciples.id"), nullable=False)
    
    # Тип инцидента
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False)  # dasha_sighting, semen_attack, light_flicker
    
    # Описание
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Уровень угрозы (1-10)
    threat_level: Mapped[int] = mapped_column(Integer, default=5)
    
    # Был ли бой с Семёном
    involved_semen: Mapped[bool] = mapped_column(Boolean, default=False)
    semen_defeated: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Дата
    reported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Связь
    disciple: Mapped["Disciple"] = relationship(back_populates="incidents")