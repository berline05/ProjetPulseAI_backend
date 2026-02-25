from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.payment_service import generate_payment_url, verify_payment, verify_webhook_signature
import json

router = APIRouter()

class PaymentRequest(BaseModel):
    userId: str
    amount: int                    # Montant en FCFA
    reason: str                    # Description ex: "Abonnement PulsAI Pro"
    name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""

class PaymentVerifyRequest(BaseModel):
    transactionId: str

# ─────────────────────────────────────────────
# CRÉER UN LIEN DE PAIEMENT
# ─────────────────────────────────────────────

@router.post("/create")
async def create_payment(request: PaymentRequest):
    """
    Génère un lien de paiement KKiaPay.
    Appelé par le frontend ou l'IA quand le client est prêt à payer.
    """
    try:
        payment_url = generate_payment_url(
            amount=request.amount,
            reason=request.reason,
            user_id=request.userId,
            name=request.name,
            email=request.email
        )
        return {
            "success": True,
            "payment_url": payment_url,
            "amount": request.amount,
            "reason": request.reason,
            "currency": "FCFA"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# VÉRIFIER UN PAIEMENT
# ─────────────────────────────────────────────

@router.post("/verify")
async def verify(request: PaymentVerifyRequest):
    """Vérifie le statut d'une transaction KKiaPay."""
    try:
        result = await verify_payment(request.transactionId)
        return {
            "success": result.get("status") == "SUCCESS",
            "status": result.get("status"),
            "amount": result.get("amount"),
            "transaction_id": request.transactionId
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# WEBHOOK KKIAPAY (confirmation automatique)
# ─────────────────────────────────────────────

@router.post("/webhook")
async def kkiapay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Reçoit les confirmations de paiement de KKiaPay.
    KKiaPay appelle cet endpoint automatiquement après chaque paiement.
    """
    body = await request.body()
    signature = request.headers.get("x-kkiapay-signature", "")

    # Vérifier la signature
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=403, detail="Signature invalide")

    data = json.loads(body)
    transaction_id = data.get("transactionId")
    status = data.get("status")
    amount = data.get("amount")
    user_id = data.get("data")  # userId passé lors de la création

    print(f"[KKiaPay] Transaction {transaction_id} | Statut: {status} | Montant: {amount} FCFA | User: {user_id}")

    if status == "SUCCESS":
        # TODO: Mettre à jour la conversation en DB, envoyer confirmation WhatsApp
        print(f"[KKiaPay] ✅ Paiement confirmé pour {user_id} — {amount} FCFA")

    return {"received": True}


# ─────────────────────────────────────────────
# PLANS TARIFAIRES
# ─────────────────────────────────────────────

@router.get("/plans")
def get_plans():
    """Retourne les plans tarifaires disponibles."""
    return {
        "plans": [
            {
                "id": "starter",
                "name": "Starter",
                "price": 9900,
                "currency": "FCFA",
                "period": "mois",
                "features": ["1 canal", "500 messages/mois", "Support email"]
            },
            {
                "id": "pro",
                "name": "Pro",
                "price": 29900,
                "currency": "FCFA",
                "period": "mois",
                "features": ["5 canaux", "5000 messages/mois", "WhatsApp inclus", "Support prioritaire"]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 99900,
                "currency": "FCFA",
                "period": "mois",
                "features": ["Canaux illimités", "Messages illimités", "IA personnalisée", "Support dédié"]
            }
        ]
    }