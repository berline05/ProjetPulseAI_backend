import os
import hmac
import hashlib
import httpx
from dotenv import load_dotenv
load_dotenv()

KKIAPAY_PUBLIC_KEY = os.getenv("KKIAPAY_PUBLIC_KEY")
KKIAPAY_PRIVATE_KEY = os.getenv("KKIAPAY_PRIVATE_KEY")
KKIAPAY_SECRET_KEY = os.getenv("KKIAPAY_SECRET_KEY")
KKIAPAY_SANDBOX = os.getenv("KKIAPAY_SANDBOX", "true").lower() == "true"

BASE_URL = "https://api-sandbox.kkiapay.me" if KKIAPAY_SANDBOX else "https://api.kkiapay.me"

async def verify_payment(transaction_id: str) -> dict:
    """Vérifie le statut d'un paiement KKiaPay."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/transactions/status",
            json={"transactionId": transaction_id},
            headers={
                "x-private-key": KKIAPAY_PRIVATE_KEY,
                "Content-Type": "application/json"
            }
        )
        return response.json()

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Vérifie la signature du webhook KKiaPay."""
    expected = hmac.new(
        KKIAPAY_SECRET_KEY.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def generate_payment_url(amount: int, reason: str, user_id: str, name: str = "", email: str = "") -> str:
    """
    Génère un lien de paiement KKiaPay.
    amount: montant en FCFA
    reason: description du paiement
    """
    sandbox_param = "sandbox" if KKIAPAY_SANDBOX else ""
    url = (
        f"https://widget.kkiapay.me"
        f"?amount={amount}"
        f"&reason={reason}"
        f"&key={KKIAPAY_PUBLIC_KEY}"
        f"&data={user_id}"
        f"&name={name}"
        f"&email={email}"
        f"&theme=%230055FF"
        f"&{'sandbox=1' if KKIAPAY_SANDBOX else ''}"
    )
    return url