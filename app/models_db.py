import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import enum

class ChannelEnum(str, enum.Enum):
    web = "web"
    whatsapp = "whatsapp"
    email = "email"
    messenger = "messenger"
    instagram = "instagram"

class StageEnum(str, enum.Enum):
    greeting = "greeting"
    qualification = "qualification"
    presentation = "presentation"
    objection = "objection"
    payment = "payment"
    completed = "completed"

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    channel = Column(SAEnum(ChannelEnum), nullable=False)
    stage = Column(SAEnum(StageEnum), default=StageEnum.greeting)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")

class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    channel = Column(SAEnum(ChannelEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    timestamp = Column(DateTime, default=datetime.utcnow)
    conversation = relationship("Conversation", back_populates="messages")
