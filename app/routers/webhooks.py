from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.ai_service import get_ai_response
from app.services.whatsapp_service import send_whatsapp_message
import os

router = APIRouter()

# ─────────────────────────────────────────────
# WHATSAPP TWILIO
# ─────────────────────────────────────────────

@router.post("/whatsapp/twilio")
async def whatsapp_twilio_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Reçoit les messages WhatsApp entrants via Twilio Sandbox.
    Twilio envoie les données en form-data (pas JSON).
    """
    form = await request.form()

    # Extraire les données du message
    from_number = form.get("From", "")      # ex: whatsapp:+22959085540
    to_number = form.get("To", "")          # ex: whatsapp:+14155238886
    body = form.get("Body", "").strip()     # Le texte du message
    profile_name = form.get("ProfileName", "Utilisateur")

    print(f"[WhatsApp] De {from_number} ({profile_name}): {body}")

    if not body or not from_number:
        return PlainTextResponse("OK")

    # Nettoyer le numéro pour l'utiliser comme userId
    user_id = from_number.replace("whatsapp:", "")

    try:
        # Appeler l'IA
        ai_response = await get_ai_response(
            user_text=body,
            history=[],
            channel="whatsapp",
            user_id=user_id,
            stage="greeting",
            db=db
        )

        # Envoyer la réponse IA via WhatsApp
        await send_whatsapp_message(from_number, ai_response["text"])

        # Si l'IA génère un lien de paiement, l'envoyer aussi
        if ai_response.get("payment_url"):
            await send_whatsapp_message(
                from_number,
                f"💳 Lien de paiement sécurisé : {ai_response['payment_url']}"
            )

    except Exception as e:
        print(f"[WhatsApp] Erreur traitement: {str(e)}")
        await send_whatsapp_message(
            from_number,
            "Désolé, une erreur est survenue. Veuillez réessayer."
        )

    # Twilio attend une réponse 200 vide ou TwiML
    return PlainTextResponse("OK")


# ─────────────────────────────────────────────
# WHATSAPP META (pour plus tard)
# ─────────────────────────────────────────────

@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "pulsai_whatsapp_token")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Token invalide")

@router.post("/whatsapp")
async def whatsapp_meta_webhook(request: Request):
    return {"status": "ok"}


# ─────────────────────────────────────────────
# MESSENGER / INSTAGRAM
# ─────────────────────────────────────────────

@router.get("/messenger")
async def messenger_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    expected_token = os.getenv("MESSENGER_VERIFY_TOKEN", "pulsai_messenger_token")
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        return PlainTextResponse(hub_challenge)
    raise HTTPException(status_code=403, detail="Token invalide")

@router.post("/messenger")
async def messenger_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    channel = "messenger" if body.get("object") == "page" else "instagram"
    try:
        for entry in body.get("entry", []):
            for messaging in entry.get("messaging", []):
                sender_id = messaging.get("sender", {}).get("id")
                text = messaging.get("message", {}).get("text", "")
                if sender_id and text:
                    print(f"[{channel.upper()}] De {sender_id}: {text}")
                    # TODO: Répondre via Graph API
    except Exception as e:
        print(f"[{channel}] Erreur: {str(e)}")
    return {"status": "ok"}


# ─────────────────────────────────────────────
# EMAIL
# ─────────────────────────────────────────────

@router.post("/email")
async def email_webhook(request: Request):
    form = await request.form()
    from_email = form.get("from", "")
    subject = form.get("subject", "")
    body = form.get("text", form.get("body-plain", ""))
    print(f"[EMAIL] De {from_email} | Sujet: {subject}")
    # TODO: Répondre par email + appeler l'IA
    return {"status": "ok"}