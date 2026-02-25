import os, time, json
from dotenv import load_dotenv
load_dotenv()

from groq import AsyncGroq
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.conversation_service import (
    get_or_create_conversation,
    save_message,
    update_conversation_stage,
    get_conversation_history
)
from app.services.payment_service import generate_payment_url

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Tu es PulsAI, un assistant commercial intelligent et empathique pour une plateforme CRM multi-canaux.
Guide le client a travers ces 6 etapes jusqu'au paiement :

1. greeting : Accueil chaleureux, comprendre le besoin du client
2. qualification : Identifier profil, budget, urgence, nombre de canaux voulus
3. presentation : Proposer le plan adapte parmi :
   - Starter : 9 900 FCFA/mois (1 canal, 500 messages)
   - Pro : 29 900 FCFA/mois (5 canaux, WhatsApp inclus)
   - Enterprise : 99 900 FCFA/mois (illimite, IA personnalisee)
4. objection : Repondre aux questions, rassurer sur la securite et la qualite
5. payment : Le client accepte — indique payment_url=GENERATE et le plan choisi dans actions
6. completed : Remercier, confirmer l'acces

IMPORTANT sur le paiement : Quand le client est pret a payer, mets "payment_url": "GENERATE" et dans "actions" mets le plan choisi ex: ["plan:pro", "amount:29900"]

Reponds TOUJOURS uniquement en JSON valide, sans texte avant ou apres :
{"text": "ta reponse", "stage": "greeting|qualification|presentation|objection|payment|completed", "payment_url": null, "actions": []}"""

PLANS = {
    "starter": 9900,
    "pro": 29900,
    "enterprise": 99900
}

async def get_ai_response(user_text: str, history: list, channel: str, user_id: str, stage: str, metadata: dict = {}, db: AsyncSession = None):
    """Appelle Groq, persiste en PostgreSQL et génère le lien KKiaPay si nécessaire."""

    conversation = None
    if db:
        conversation = await get_or_create_conversation(db, user_id, channel)
        await save_message(db, conversation.id, "user", user_text, channel)

    # Construire l'historique
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in history[-10:]:
        role = m.role if hasattr(m, 'role') else m.get('role', 'user')
        content = m.content if hasattr(m, 'content') else m.get('content', '')
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_text})

    # Appel Groq
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
    actions = data.get("actions", [])
    payment_url = None

    # Générer le lien KKiaPay si l'IA le demande
    if data.get("payment_url") == "GENERATE":
        # Détecter le plan depuis les actions
        plan = "pro"
        amount = PLANS["pro"]
        for action in actions:
            if action.startswith("plan:"):
                plan = action.split(":")[1]
                amount = PLANS.get(plan, PLANS["pro"])
            if action.startswith("amount:"):
                amount = int(action.split(":")[1])

        payment_url = generate_payment_url(
            amount=amount,
            reason=f"PulsAI {plan.capitalize()} — {amount} FCFA/mois",
            user_id=user_id
        )
        ai_text += f"\n\n💳 Voici votre lien de paiement sécurisé KKiaPay :\n{payment_url}"

    # Persister la réponse IA
    if db and conversation:
        await save_message(db, conversation.id, "assistant", ai_text, channel)
        await update_conversation_stage(db, conversation.id, new_stage)

    return {
        "text": ai_text,
        "stage": new_stage,
        "timestamp": int(time.time() * 1000),
        "payment_url": payment_url,
        "actions": actions,
        "from_": "ia"
    }

async def get_channel_history(user_id: str, channel: str, limit: int = 50, db: AsyncSession = None) -> list:
    if db:
        return await get_conversation_history(db, user_id, channel, limit)
    return []
