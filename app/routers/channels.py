from fastapi import APIRouter, HTTPException

router = APIRouter()

SUPPORTED_CHANNELS = [
    {"id": "web", "label": "Chat Web", "icon": "globe", "active": True},
    {"id": "whatsapp", "label": "WhatsApp", "icon": "phone", "active": True},
    {"id": "email", "label": "Email", "icon": "mail", "active": True},
    {"id": "messenger", "label": "Messenger", "icon": "message", "active": True},
    {"id": "instagram", "label": "Instagram", "icon": "camera", "active": True},
]

@router.get("/")
def list_channels():
    return {"channels": SUPPORTED_CHANNELS}

@router.get("/{channel}/status")
def channel_status(channel: str):
    ch = next((c for c in SUPPORTED_CHANNELS if c["id"] == channel), None)
    if not ch:
        raise HTTPException(status_code=404, detail=f"Canal '{channel}' inconnu")
    return {"channel": channel, "status": "active", "connected": ch["active"]}
