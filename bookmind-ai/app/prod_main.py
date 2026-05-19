from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from datetime import datetime

# Proje kök dizinini Python yoluna ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Kendi servisimizi import edelim
from app.service.chatbot import get_rag_response

app = FastAPI(title="BookMind AI API - Production", version="1.1.0")

# CORS Ayarları: Her yerden erişime izin ver (Canlı ortam için önemli)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str

@app.get("/")
def home():
    return {
        "status": "online", 
        "message": "BookMind AI Canli Sunucusu Calisiyor",
        "timestamp": str(datetime.now())
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = get_rag_response(request.message, request.user_id)
        return {
            "success": True,
            "reply": response,
            "timestamp": str(datetime.now())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Render.com için dinamik PORT ayarı
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
