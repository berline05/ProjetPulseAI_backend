from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.schemas import AIMessageRequest
from app.services.ai_service import get_ai_response, get_channel_history
from app.database import get_db

router = APIRouter()

@router.post("/message")
async def send_message(request: AIMessageRequest, db: AsyncSession = Depends(get_db)):
    """Endpoint principal — reçoit un message et retourne la réponse IA persistée en DB."""
    try:
        response = await get_ai_response(
            user_text=request.text,
            history=request.history or [],
            channel=request.channel.value,
            user_id=request.userId,
            stage=request.stage,
            metadata=request.metadata or {},
            db=db
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{user_id}/{channel}")
async def get_messages(user_id: str, channel: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Récupère l'historique des messages depuis PostgreSQL."""
    try:
        messages = await get_channel_history(user_id, channel, limit, db)
        return {"messages": messages, "userId": user_id, "channel": channel}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stage/{user_id}/{channel}")
async def get_stage(user_id: str, channel: str, db: AsyncSession = Depends(get_db)):
    """Retourne le stade actuel de la conversation."""
    from app.conversation_service import get_or_create_conversation
    conversation = await get_or_create_conversation(db, user_id, channel)
    return {"userId": user_id, "channel": channel, "stage": conversation.stage}