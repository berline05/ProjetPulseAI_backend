from pydantic import BaseModel
from typing import Optional, Literal, List
from enum import Enum

class Channel(str, Enum):
    web = "web"
    whatsapp = "whatsapp"
    email = "email"
    messenger = "messenger"
    instagram = "instagram"

class ConversationStage(str, Enum):
    greeting = "greeting"
    qualification = "qualification"
    presentation = "presentation"
    objection = "objection"
    payment = "payment"
    completed = "completed"

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class AIMessageRequest(BaseModel):
    userId: str
    channel: Channel
    text: str
    history: Optional[List[Message]] = []
    stage: Optional[ConversationStage] = ConversationStage.greeting
    metadata: Optional[dict] = {}

class AIMessageResponse(BaseModel):
    text: str
    from_: str = "ia"
    stage: ConversationStage
    timestamp: int
    payment_url: Optional[str] = None
    actions: Optional[List[str]] = []

class ChannelMessage(BaseModel):
    userId: str
    channel: Channel
    limit: Optional[int] = 50

class WhatsAppWebhook(BaseModel):
    object: str
    entry: Optional[List[dict]] = []

class EmailWebhook(BaseModel):
    from_email: str
    subject: str
    body: str
    message_id: str

class MessengerWebhook(BaseModel):
    object: str
    entry: Optional[List[dict]] = []