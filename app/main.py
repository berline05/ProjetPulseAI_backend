from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ai, channels, webhooks
from app.database import init_db

app = FastAPI(
    title="PulsAI CRM Backend",
    description="Backend multi-canaux avec IA conversationnelle jusqu'au paiement",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(ai.router, prefix="/api/ai", tags=["IA"])
app.include_router(channels.router, prefix="/api/channels", tags=["Canaux"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])

@app.get("/")
def root():
    return {"status": "PulsAI backend running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}