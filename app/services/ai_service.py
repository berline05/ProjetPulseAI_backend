import os, time, json
from dotenv import load_dotenv
load_dotenv()

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.conversation_service import (
    get_or_create_conversation,
    save_message,
    update_conversation_stage,
    get_conversation_history
)

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Tu es PulsAI, un assistant commercial intelligent et empathique pour une plateforme CRM.
Guide le client a travers ces 6 etapes jusqu'au paiement :
1. greeting : Accueil chaleureux, comprendre le besoin
2. qualification : Identifier profil, budget, urgence
3. presentation : Proposer la solution adaptee avec prix
4. objection : Repondre aux questions, rassurer
5. payment : Proposer le lien de paiement, conclure
6. completed : Remercier, confirmer la commande

Reponds TOUJOURS uniquement en JSON valide, sans texte avant ou apres :
{"text": "ta reponse", "stage": "greeting|qualification|presentation|objection|payment|completed", "payment_url": null, "actions": []}"""

async def get_ai_response(user_text, history, channel, user_id, stage, metadata={}, db=None):
    conversation = None
    if db:
        conversation = await get_or_create_conversation(db, user_id, channel)
        await save_message(db, conversation.id, "user", user_text, channel)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-10:]:
        role = m.role if hasattr(m, "role") else m.get("role", "user")
        content = m.content if hasattr(m, "content") else m.get("content", "")
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
        temperature=0.7,
    )
    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except Exception:
        data = {"text": raw, "stage": stage, "payment_url": None, "actions": []}

    ai_text = data.get("text", "Je suis la pour vous aider!")
    new_stage = data.get("stage", stage)

    if db and conversation:
        await save_message(db, conversation.id, "assistant", ai_text, channel)
        await update_conversation_stage(db, conversation.id, new_stage)

    return {
        "text": ai_text,
        "stage": new_stage,
        "timestamp": int(time.time() * 1000),
        "payment_url": data.get("payment_url"),
        "actions": data.get("actions", []),
        "from_": "ia"
    }

async def get_channel_history(user_id, channel, limit=50, db=None):
    if db:
        return await get_conversation_history(db, user_id, channel, limit)
    return []
