from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
import hmac, hashlib, os, json

router = APIRouter()

# ─────────────────────────────────────────────
# WHATSAPP (Meta Business API)
# ─────────────────────────────────────────────

@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Vérification du webhook WhatsApp par Meta."""
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "pulsai_whatsapp_token")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Reçoit les messages entrants WhatsApp.
    Meta envoie un payload JSON avec les messages.
    """
    body = await request.json()

    # Vérifier la signature (sécurité)
    # signature = request.headers.get("X-Hub-Signature-256", "")
    # TODO: valider la signature avec APP_SECRET

    try:
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    if msg.get("type") == "text":
                        user_phone = msg["from"]
                        text = msg["text"]["body"]
                        msg_id = msg["id"]
                        print(f"[WhatsApp] De {user_phone}: {text}")
                        # TODO: Appeler ai_service.get_ai_response() et renvoyer via WhatsApp API
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# MESSENGER & INSTAGRAM (Meta)
# ─────────────────────────────────────────────

@router.get("/messenger")
async def messenger_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    """Vérification du webhook Messenger/Instagram par Meta."""
    expected_token = os.getenv("MESSENGER_VERIFY_TOKEN", "pulsai_messenger_token")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Token de vérification invalide")

@router.post("/messenger")
async def messenger_webhook(request: Request):
    """
    Reçoit les messages Messenger & Instagram.
    Le canal (messenger vs instagram) est déterminé par le champ 'object'.
    """
    body = await request.json()
    channel = "messenger" if body.get("object") == "page" else "instagram"

    try:
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                message = messaging.get("message", {})
                text = message.get("text", "")
                if sender_id and text:
                    print(f"[{channel.upper()}] De {sender_id}: {text}")
                    # TODO: Appeler ai_service.get_ai_response() et renvoyer via Graph API
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# EMAIL (via SendGrid / Mailgun Inbound)
# ─────────────────────────────────────────────

@router.post("/email")
async def email_webhook(request: Request):
    """
    Reçoit les emails entrants via SendGrid Inbound Parse ou Mailgun Routes.
    """
    form = await request.form()
    from_email = form.get("from", "")
    subject = form.get("subject", "")
    body = form.get("text", form.get("body-plain", ""))
    message_id = form.get("Message-Id", "")

    print(f"[EMAIL] De {from_email} | Sujet: {subject}")
    print(f"Contenu: {body[:200]}...")

    # TODO: Appeler ai_service.get_ai_response() et répondre par email
    return {"status": "ok", "received": True}