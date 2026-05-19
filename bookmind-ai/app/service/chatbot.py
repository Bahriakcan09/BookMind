import os
import logging
import sys

# ===== [KRITIK] LOGGING ILK SIRADA OLMALI =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ],
    force=True 
)
logger = logging.getLogger(__name__)

import json
import re
import time
import difflib
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional, Set

# ===== [SAGLAMCI] OTOMATIK YOL BULMA =====
current_script_dir = os.path.dirname(os.path.abspath(__file__))
if "app" in current_script_dir:
    project_root = os.path.abspath(os.path.join(current_script_dir, "..", ".."))
else:
    project_root = os.path.abspath(os.path.join(current_script_dir, ".."))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

env_path = os.path.join(project_root, ".env")
load_dotenv(env_path)

# LangChain & Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# Kendi modüllerimiz
try:
    from lib.embeddings import embed_text, find_similar_books
    from lib.firebase_db import fb_manager
    logger.info("Moduller ve Firebase baglantisi hazirlaniyor... [OK]")
except ImportError as e:
    logger.error(f"Modul yuklenemedi: {e}")
    sys.exit(1)

# ===== AYARLAR VE GIZLI VERI =====
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.error("Hata: GOOGLE_API_KEY bulunamadi!")
    sys.exit(1)

# ===== LLM KURULUMU =====
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        api_key=GOOGLE_API_KEY,
        temperature=0.3,
        timeout=30,
        max_retries=2
    )
    logger.info("Gemini 2.5 Flash LLM basariyla yuklendi [OK]")
except Exception as e:
    logger.error(f"LLM başlatma hatası: {e}")
    sys.exit(1)

# ===== BELLEK (MEMORY) KURULUMU =====
# Her kullanıcı için ayrı hafıza tutacak şekilde geliştirilebilir
chat_history = ChatMessageHistory()

# ===== KİTAP VERİLERİ YÜKLEME =====
BOOKS_PATH = os.path.join(project_root, 'data', 'books_with_embeddings.json')
try:
    with open(BOOKS_PATH, 'r', encoding='utf-8') as f:
        ALL_BOOKS = json.load(f)
    logger.info(f"Toplam {len(ALL_BOOKS)} kitap katalogdan yuklendi [OK]")
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
    },
    "YARDIM": {
        "tetikleyiciler": ["yardım", "help", "ne yapabilirsin", "nasıl kullanılır"],
        "cevap": "Ben sizin akıllı kitap danışmanınızım. Size türlere göre öneri yapabilir, kütüphanenizdeki kitapları yorumlayabilir veya yazarlara göre kitap bulabilirim."
    }
}

# ===== PROMPT TEMPLATE (OZ VE ETKILEYICI KITAP KURDU) =====
PROMPT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """Sen BookMind platformunun tutkulu ve bilgili bir kitap danışmanısın. Gerçek bir kitap kurdu gibi ama öz konuş.

GÖREVİN:
1. SANA VERİLEN KULLANICI GEÇMİŞİ'ni (Kütüphane ve Sepet) hızlıca analiz et.
2. KİTAP LİSTESİ içinden kullanıcıya en uygun MAKSİMUM 3 kitap seç.
3. Önerilerini yaparken kullanıcının geçmişiyle edebi bağlar kur ama lafı uzatma.
4. Her kitap açıklamasını en fazla 2-3 etkileyici cümle ile sınırla.
5. KESİNLİKLE özür dileme, hatalardan bahsetme. 
6. Teknik terimleri ve emojileri asla kullanma.

KULLANICI GEÇMİŞİ:
{user_history}

KİTAP LİSTESİ:
{context}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

# ===== ENDUSTRIYEL YAPILAR =====
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

class RecommendationTracker:
    def __init__(self):
        self.recommended_titles: Set[str] = set()
    
    def mark_recommended(self, book: Dict):
        self.recommended_titles.add(book['title'])
    
    def is_already_recommended(self, book: Dict) -> bool:
        return book['title'] in self.recommended_titles

recommendation_tracker = RecommendationTracker()

# ===== TEMEL FONKSİYONLAR =====
def sanitize_input(question: str, max_length: int = 500) -> str:
    question = question.strip()
    if len(question) > max_length: question = question[:max_length]
    return question

def apply_rule_based_filter(question: str) -> Optional[str]:
    q_lower = question.lower().strip()
    for rule_name, rule_data in RULES.items():
        for trigger in rule_data["tetikleyiciler"]:
            if rf"\b{re.escape(trigger)}\b" in q_lower:
                return rule_data["cevap"]
    return None

def extract_search_intent(question: str) -> str:
    noise = ["başka", "daha", "var mı", "öner", "kitabı", "kitapları", "lütfen", "koleksiyonunuzda", "mevcut", "mu"]
    search_intent = question.lower()
    for word in noise:
        search_intent = re.sub(rf"\b{re.escape(word)}\b", " ", search_intent, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', search_intent).strip()

def invoke_llm_with_retry(messages, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            if not rate_limiter.can_request(): time.sleep(30)
            time.sleep(3)
            logger.info(f"Gemini API çağrısı yapılıyor (Deneme {attempt + 1})...")
            response = llm.invoke(messages)
            rate_limiter.record_request()
            return response.content
        except Exception as e:
            logger.error(f"API Hatası: {e}")
            time.sleep(10 * (attempt + 1))
    return "Üzgünüm, şu an yanıt üretemiyorum."

def get_rag_response(question: str, user_id: str) -> str:
    # 1. Kural Kontrolü
    rule_response = apply_rule_based_filter(question)
    if rule_response: return rule_response
    
    # 2. Canli Kullanici Verilerini Cek (Gelen ID'ye gore)
    user_context = fb_manager.get_user_context(user_id)
    logger.info(f"Canli kullanıcı verisi yuklendi ({user_id})")
    
    # 3. Akıllı Arama
    search_query = extract_search_intent(question)
    if len(search_query) < 3 and len(chat_history.messages) >= 2:
        last_user_msg = chat_history.messages[-2].content
        search_query = extract_search_intent(last_user_msg)
        logger.info(f"Hafızadan konu geri çağrıldı: '{search_query}'")

    logger.info(f"Vektör araması başlatıldı: '{search_query}'")
    query_vector = embed_text(search_query)
    similar_books = find_similar_books(query_vector, ALL_BOOKS, top_k=10)

    # 4. HIBRIT YAZAR YAKALAMA
    clean_name = re.sub(r"(kitapları|kitabı|öner|bul|var mı|mevcut|mu|koleksiyonunuzda)", "", question.lower()).strip()
    if len(clean_name) > 3:
        all_authors = list(set(b.get('author', '') for b in ALL_BOOKS))
        close_matches = difflib.get_close_matches(clean_name, [a.lower() for a in all_authors], n=1, cutoff=0.5)
        if close_matches:
            target = close_matches[0]
            logger.info(f"Yazar eşleşmesi yakalandı: {target}")
            for b in ALL_BOOKS:
                if b.get('author', '').lower() == target:
                    if not any(sb['id'] == b['id'] for sb in similar_books):
                        b_copy = b.copy()
                        b_copy['similarity'] = 0.99
                        similar_books.insert(0, b_copy)

    # 5. Context Oluşturma
    context_text = ""
    for b in similar_books:
        if not recommendation_tracker.is_already_recommended(b['title']):
            context_text += f"Başlık: {b['title']}, Yazar: {b['author']}, Tür: {b.get('genre', '')}, Özet: {b['description'][:200]}\n\n"
    
    try:
        messages = PROMPT_TEMPLATE.format_messages(
            context=context_text if context_text else "Ek kitap bulunamadı.",
            user_history=user_context['history_text'],
            question=question,
            chat_history=chat_history.messages
        )
        
        response_content = invoke_llm_with_retry(messages)
        chat_history.add_user_message(question)
        chat_history.add_ai_message(response_content)
        
        for book in similar_books[:2]:
            recommendation_tracker.mark_recommended(book['title'])
            
        return response_content
    except Exception as e:
        return f"Sistem hatası: {str(e)}"

def start_chat():
    # Terminal testleri için varsayılan bir ID kullanalım
    TEST_USER_ID = "22coPPxc9pNy3XevLbPhhSpsGjr1"
    print("\n" + "="*60)
    print("BookMind Akıllı Asistanı Yayında! (Dinamik Entegrasyon Modu)")
    print("="*60 + "\n")
    
    while True:
        user_input = input("\n👤 Siz: ").strip()
        if not user_input or user_input.lower() == 'q':
            print("\nAsistan: Hoşça kalın!")
            break
        print(f"\n🤖 Asistan:\n{get_rag_response(user_input, TEST_USER_ID)}")

if __name__ == "__main__":
    start_chat()
