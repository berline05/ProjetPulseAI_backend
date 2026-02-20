// services/ai.js
// Service qui communique avec le backend PulsAI FastAPI

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Envoie un message à l'IA et retourne sa réponse.
 * Appelé par ChatWidget.jsx
 */
export async function fetchIAResponse({ userId, channel, text, history = [], stage = 'greeting', metadata = {} }) {
  const response = await fetch(`${API_BASE}/api/ai/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId, channel, text, history, stage, metadata }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Erreur serveur: ${response.status}`);
  }

  return response.json();
}

/**
 * Récupère l'historique des messages d'un utilisateur sur un canal.
 * Appelé au chargement du ChatWidget.
 */
export async function fetchChannelMessages(userId, channel) {
  try {
    const response = await fetch(`${API_BASE}/api/ai/messages/${userId}/${channel}`);
    if (!response.ok) return [];
    const data = await response.json();
    return data.messages || [];
  } catch {
    return [];
  }
}