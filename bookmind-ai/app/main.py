from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Proje kok dizinini Python yoluna ekle
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Kendi servislerimizi import edelim
# Not: Mevcut chatbot mantığını bir fonksiyona bağlayacağız
from app.service.chatbot import get_rag_response

app = FastAPI(title="BookMind AI API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme aşamasında her yerden erişime izin ver
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# İstek (Request) Modeli bu değiştirilecek daha sonra, şu an için sadece mesaj ve kullanıcı ID'si alacağız 
class ChatRequest(BaseModel):
    message: str
    user_id: str = "22coPPxc9pNy3XevLbPhhSpsGjr1" # Varsayılan olarak senin ID'n

@app.get("/")
def home():
    return {"status": "online", "message": "BookMind AI Sunucusu Calisiyor"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Kullanıcı mesajını alır, chatbot mantığını çalıştırır ve cevabı döner.
    """
    try:
        # Chatbot çekirdeğini çalıştır
        response = get_rag_response(request.message)
        
        return {
            "success": True,
            "reply": response,
            "timestamp": str(datetime.now())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    uvicorn.run(app, host="0.0.0.0", port=8000)
