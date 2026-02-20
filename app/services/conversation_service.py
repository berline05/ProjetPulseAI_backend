from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from app.models_db import Conversation, Message, StageEnum
from datetime import datetime
import uuid

async def get_or_create_conversation(db: AsyncSession, user_id: str, channel: str) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .where(Conversation.channel == channel)
        .where(Conversation.stage != StageEnum.completed)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    conversation = result.scalars().first()
    if not conversation:
        conversation = Conversation(user_id=user_id, channel=channel, stage=StageEnum.greeting)
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
    return conversation

async def save_message(db: AsyncSession, conversation_id: uuid.UUID, role: str, content: str, channel: str) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content, channel=channel, timestamp=datetime.utcnow())
    db.add(message)
    await db.execute(update(Conversation).where(Conversation.id == conversation_id).values(updated_at=datetime.utcnow()))
    await db.commit()
    await db.refresh(message)
    return message

async def update_conversation_stage(db: AsyncSession, conversation_id: uuid.UUID, stage: str):
    await db.execute(update(Conversation).where(Conversation.id == conversation_id).values(stage=stage, updated_at=datetime.utcnow()))
    await db.commit()

async def get_conversation_history(db: AsyncSession, user_id: str, channel: str, limit: int = 50) -> list:
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .where(Conversation.channel == channel)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    conversation = result.scalars().first()
    if not conversation:
        return []
    return [{"from": "user" if msg.role == "user" else "ia", "text": msg.content, "timestamp": int(msg.timestamp.timestamp() * 1000)} for msg in conversation.messages[-limit:]]
