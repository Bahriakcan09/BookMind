import os
import json
import sys
import re
import time
import random
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional

# LangChain & Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# Logging Kurulumu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bookmind.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# .env yükle
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.error("Hata: GOOGLE_API_KEY bulunamadi! Lutfen .env dosyanizi kontrol edin.")
    sys.exit(1)

logger.info("API Anahtari yuklendi [OK]")

# Kendi modüllerimiz
sys.path.append(os.getcwd())
try:
    from lib.embeddings import embed_text, find_similar_books
    logger.info("Embedding modulu yuklendi [OK]")
except ImportError as e:
    logger.error(f"Embedding modulu yuklenemedi: {e}")
    sys.exit(1)

# ===== LLM KURULUMU =====
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        api_key=GOOGLE_API_KEY,
        temperature=0.7,
        timeout=30,
        max_retries=2
    )
    logger.info("Gemini 2.5 Flash LLM basariyla yuklendi [OK]")
except Exception as e:
    logger.error(f"LLM başlatma hatası: {e}")
    sys.exit(1)

# ===== BELLEK (MEMORY) KURULUMU =====
demo_ephemeral_chat_history = ChatMessageHistory()

# ===== KİTAP VERİLERİ YÜKLEME =====
BOOKS_PATH = os.path.join('data', 'books_with_embeddings.json')
try:
    with open(BOOKS_PATH, 'r', encoding='utf-8') as f:
        ALL_BOOKS = json.load(f)
    logger.info(f"Toplam {len(ALL_BOOKS)} kitap yuklendi [OK]")
except Exception as e:
    logger.error(f"Veri yukleme hatasi: {e}")
    sys.exit(1)

# ===== KURAL BAZLI FİLTRELER =====
RULES = {
    "SELAMLAMA": {
        "tetikleyiciler": ["merhaba", "selam", "hi", "hey", "gunaydin", "iyi gunler", "selamlar"],
        "cevap": "Merhaba! Size kitap önerileri konusunda yardımcı olabilirim. Ne tür kitap arıyorsunuz?"
    },
    "TESEKKUR": {
        "tetikleyiciler": ["tesekkur", "sağol", "thanks", "tesekkurler", "cok sagol"],
        "cevap": "Rica ederim! Başka bir kitap önerisi ister misiniz?"
    },
    "KONU_DISI": {
        "tetikleyiciler": ["hava", "durum", "futbol", "yemek", "matematik", "kod", "sarki", "nasilisin"],
        "cevap": "Üzgünüm, ben sadece kitap önerileri konusunda yardımcı olabilirim. Size bir kitap önermemi ister misiniz?"
    }
}

# ===== PROMPT TEMPLATE =====
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """Sen BookMind platformunun çok dikkatli bir kitap danışmanısın.
   
GÖREVİN:
- Aşağıdaki KİTAP LİSTESİ'ni satır satır incele.
- Kullanıcı bir yazar (örneğin Agatha Christie) sorduğunda, listede o yazarın ismini görüyorsan kesinlikle "yok" deme, o kitabı öner.
- Teknik terimleri (CONTEXT, liste vb.) asla kullanma.
- Emojileri asla kullanma.
- Eğer aranan yazar listede gerçekten yoksa, "Bu yazara ait bir kitabımız şu an yok ama polisiye sevdiğiniz için şunlar var" diyerek benzerlerini öner.
- Maksimum 3 kitap önerisi yap.
- Samimi ve bilgili bir kütüphaneci gibi davran.

KİTAP LİSTESİ:
{context}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# ===== RATE LIMITING YAPISI =====
class RateLimiter:
    def __init__(self, requests_per_minute: int = 15, requests_per_day: int = 1500):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.request_times = []
        self.daily_count = 0
        self.last_reset = datetime.now()
    
    def can_request(self) -> bool:
        now = datetime.now()
        if (now - self.last_reset).days >= 1:
            self.daily_count = 0
            self.last_reset = now
        self.request_times = [t for t in self.request_times if (now - t).total_seconds() < 60]
        return len(self.request_times) < self.requests_per_minute and self.daily_count < self.requests_per_day
    
    def record_request(self):
        self.request_times.append(datetime.now())
        self.daily_count += 1

rate_limiter = RateLimiter()

# ===== TEMEL FONKSİYONLAR =====
def apply_rule_based_filter(question: str) -> Optional[str]:
    q_lower = question.lower().strip()
    for rule_name, rule_data in RULES.items():
        for trigger in rule_data["tetikleyiciler"]:
            pattern = rf"\b{re.escape(trigger)}\b"
            if re.search(pattern, q_lower):
                return rule_data["cevap"]
    return None

def invoke_llm_with_retry(messages, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            if not rate_limiter.can_request():
                return "Şu an çok yoğunluk var. Lütfen biraz bekleyip tekrar deneyin."
            
            time.sleep(3)
            logger.info(f"Gemini API çağrısı yapılıyor (Deneme {attempt + 1})...")
            
            response = llm.invoke(messages)
            rate_limiter.record_request()
            return response.content
        
        except Exception as e:
            logger.error(f"API hatası (Deneme {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10 * (attempt + 1))
            else:
                return f"Hata: {str(e)}"

def get_rag_response(question: str) -> str:
    rule_response = apply_rule_based_filter(question)
    if rule_response:
        return rule_response
    
    # Hafızayı aramaya dahil et
    search_query = question
    if len(demo_ephemeral_chat_history.messages) >= 2:
        last_context = demo_ephemeral_chat_history.messages[-2].content
        search_query = f"{last_context} {question}"

    # RAG: Kitap Bulma (top_k=10 yapıldı ki hiçbir yazar kaçmasın)
    logger.info(f"Vektör araması yapılıyor: '{search_query}'")
    query_vector = embed_text(search_query)
    similar_books = find_similar_books(query_vector, ALL_BOOKS, top_k=10)
    
    logger.info(f"Bulunan en yakın kitaplar:")
    context_text = ""
    for i, b in enumerate(similar_books, 1):
        similarity_score = round(b.get('similarity', 0) * 100, 2)
        logger.info(f"   {i}. {b['title']} - {b['author']} (Benzerlik: %{similarity_score})")
        context_text += f"Başlık: {b['title']}, Yazar: {b['author']}, Tür: {b['genre']}, Özet: {b['description']}\n\n"
    
    try:
        messages = PROMPT_TEMPLATE.format_messages(
            context=context_text,
            question=question,
            chat_history=demo_ephemeral_chat_history.messages
        )
        
        response_content = invoke_llm_with_retry(messages)
        
        # Hafızaya ekle
        demo_ephemeral_chat_history.add_user_message(question)
        demo_ephemeral_chat_history.add_ai_message(response_content)
        
        return response_content
    except Exception as e:
        logger.error(f"RAG yanıt oluşturma hatası: {e}")
        return f"Bir hata oluştu: {str(e)}"

def start_chat():
    print("\n" + "="*50)
    print("BookMind Akıllı Asistanı Yayında! (Agatha Düzeltmeli)")
    print("="*50)
    
    while True:
        user_input = input("\n👤 Siz: ").strip()
        if not user_input or user_input.lower() == 'q':
            break
        print(f"\n🤖 Asistan:\n{get_rag_response(user_input)}")

if __name__ == "__main__":
    start_chat()
