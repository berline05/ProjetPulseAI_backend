import os
import time
from typing import List, Optional
from anthropic import AsyncAnthropic
from app.models.schemas import Message, ConversationStage

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Prompt système : l'IA guide la conversation jusqu'au paiement
SYSTEM_PROMPT = """Tu es PulsAI, un assistant commercial intelligent et empathique pour une plateforme CRM multi-canaux.

Ton objectif est de guider chaque client à travers ces étapes :
1. **Accueil** (greeting) : Souhaiter la bienvenue, comprendre le besoin
2. **Qualification** (qualification) : Identifier le profil, budget, urgence
3. **Présentation** (presentation) : Proposer la solution adaptée avec les prix
4. **Traitement des objections** (objection) : Répondre aux questions, rassurer
5. **Paiement** (payment) : Proposer le lien de paiement sécurisé, conclure la vente
6. **Terminé** (completed) : Remercier, confirmer la commande

Règles importantes :
- Sois naturel, chaleureux, jamais robotique
- Adapte ton ton au canal (plus formel par email, plus direct sur WhatsApp)
- Ne jamais mentir sur les prix ou fonctionnalités
- Si l'utilisateur est prêt à payer, génère un lien de paiement
- Réponds TOUJOURS en JSON avec ce format exact :
{
  "text": "ta réponse visible par l'utilisateur",
  "stage": "greeting|qualification|presentation|objection|payment|completed",
  "payment_url": "https://pay.pulsai.com/checkout/xxx" ou null,
  "actions": ["bouton1", "bouton2"] ou []
}

IMPORTANT : Ne sors JAMAIS du format JSON. Pas de texte avant ou après.
"""

CHANNEL_TONE = {
    "web": "Utilise un ton professionnel mais accessible.",
    "whatsapp": "Utilise un ton décontracté, des messages courts, des emojis appropriés.",
    "email": "Utilise un ton formel avec des phrases complètes et structurées.",
    "messenger": "Utilise un ton convivial et dynamique, messages courts.",
    "instagram": "Utilise un ton moderne, inspirant, avec des emojis.",
}

async def get_ai_response(
    user_text: str,
    history: List[Message],
    channel: str,
    user_id: str,
    stage: ConversationStage,
    metadata: dict = {}
) -> dict:
    """Appelle Claude et retourne une réponse structurée."""

    # Construire le contexte du canal
    channel_instruction = CHANNEL_TONE.get(channel, CHANNEL_TONE["web"])
    system = f"{SYSTEM_PROMPT}\n\nCanal actuel : {channel.upper()}. {channel_instruction}\nStade actuel de la conversation : {stage}\nID utilisateur : {user_id}"

    # Construire l'historique des messages
    messages = []
    for msg in history[-10:]:  # Max 10 messages d'historique
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # Ajouter le message actuel
    messages.append({"role": "user", "content": user_text})

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=messages
        )

        raw = response.content[0].text.strip()

        # Parser le JSON retourné par Claude
        import json
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback si Claude n'a pas respecté le format
            data = {
                "text": raw,
                "stage": stage,
                "payment_url": None,
                "actions": []
            }

        return {
            "text": data.get("text", "Je suis là pour vous aider !"),
            "stage": data.get("stage", stage),
            "timestamp": int(time.time() * 1000),
            "payment_url": data.get("payment_url"),
            "actions": data.get("actions", []),
            "from_": "ia"
        }

    except Exception as e:
        raise RuntimeError(f"Erreur Claude API: {str(e)}")


async def get_channel_history(user_id: str, channel: str, limit: int = 50) -> List[dict]:
    """
    Récupère l'historique des messages d'un utilisateur sur un canal.
    Pour le MVP, retourne un historique vide.
    À connecter à une DB (PostgreSQL/Redis) en production.
    """
    # TODO: Connecter à la base de données
    return []