import os
from dotenv import load_dotenv
load_dotenv()

from twilio.rest import Client

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

async def send_whatsapp_message(to_number: str, text: str) -> bool:
    """
    Envoie un message WhatsApp via Twilio.
    to_number: numéro au format international ex: +22959085540
    """
    try:
        # S'assurer que le numéro est au format whatsapp:+xxx
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"

        message = client.messages.create(
            from_=TWILIO_NUMBER,
            to=to_number,
            body=text
        )
        print(f"[WhatsApp] Message envoyé à {to_number} — SID: {message.sid}")
        return True
    except Exception as e:
        print(f"[WhatsApp] Erreur envoi: {str(e)}")
        return False