import os
import json
import sys
import re
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Optional, Set

# LangChain & Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# LOGGING KURULUMU
logging.basicConfig(
    level=logging.WARNING, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
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

# LLM KURULUMU
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        api_key=GOOGLE_API_KEY,
        temperature=0.5,
        timeout=30,
        max_retries=2
    )
    logger.info("Gemini 2.5 Flash LLM basariyla yuklendi [OK]")
except Exception as e:
    logger.error(f"LLM başlatma hatası: {e}")
    sys.exit(1)

# BELLEK (MEMORY) KURULUMU 
chat_history = ChatMessageHistory()

# KİTAP VERİLERİ YÜKLEME
BOOKS_PATH = os.path.join('data', 'books_with_embeddings.json')
try:
    with open(BOOKS_PATH, 'r', encoding='utf-8') as f:
        ALL_BOOKS = json.load(f)
    logger.info(f"Toplam {len(ALL_BOOKS)} kitap yuklendi [OK]")
except Exception as e:
    logger.error(f"Veri yukleme hatasi: {e}")
    sys.exit(1)

# KURAL BAZLI FİLTRELER 
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

# RATE LIMITING YAPISI =
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
        self.recommended_authors: Dict[str, int] = {}
    
    def mark_recommended(self, book: Dict):
        self.recommended_titles.add(book['title'])
        author = book['author']
        self.recommended_authors[author] = self.recommended_authors.get(author, 0) + 1
        logger.info(f"Onerilen: {book['title']} - {author}")
    
    def is_already_recommended(self, book: Dict) -> bool:
        return book['title'] in self.recommended_titles
    
    def get_recommended_count(self) -> int:
        return len(self.recommended_titles)
    
    def reset(self):
        self.recommended_titles.clear()
        self.recommended_authors.clear()

recommendation_tracker = RecommendationTracker()

#
def sanitize_input(question: str, max_length: int = 500) -> str:
    question = question.strip()
    
    if len(question) > max_length:
        logger.warning(f"Input cok uzun ({len(question)} chars), kisaltiliyor")
        question = question[:max_length]
    
    if not question:
        return ""
    
    return question

def apply_rule_based_filter(question: str) -> Optional[str]:
    q_lower = question.lower().strip()
    for rule_name, rule_data in RULES.items():
        for trigger in rule_data["tetikleyiciler"]:
            pattern = rf"\b{re.escape(trigger)}\b"
            if re.search(pattern, q_lower):
                return rule_data["cevap"]
    return None

def extract_search_intent(question: str, chat_history_obj: ChatMessageHistory) -> str:
    
    context_words = [
        "başka", "daha", "ayrıca", "bir de", "bir tane daha",
        "var mı", "bana", "sana", "lütfen", "rica ederim", "söyler misin",
        "öner misin", "bulabilir misin", "yapabilir misin", "kitaplari", "kitapları"
    ]
    
    search_intent = question.lower()
    
    for word in context_words:
        search_intent = re.sub(rf"\b{re.escape(word)}\b", " ", search_intent, flags=re.IGNORECASE)
    
    search_intent = re.sub(r'\s+', ' ', search_intent).strip()
    
    logger.info(f"Orijinal soru: '{question}'")
    logger.info(f"Search intent: '{search_intent}'")
    
    # GÜNCELLEME: Hem Kitap Adı hem Yazar alanına ekleyerek aramayı güçlendiriyoruz
    formatted_query = f"KİTAP ADI: {search_intent}\nYAZAR: {search_intent}\nTÜR:\nÖZET: {search_intent}"
    logger.info(f"Formatted query: '{formatted_query[:60]}...'")
    
    return formatted_query

def build_context_text(similar_books: List[Dict]) -> str:
    context_text = ""
    
    for book in similar_books:
        context_text += (
            f"Baslik: {book['title']}, "
            f"Yazar: {book['author']}, "
            f"Tur: {book.get('genre', 'N/A')}, "
            f"Ozet: {book.get('description', 'N/A')[:200]}\n\n"
        )
    
    if not context_text:
        context_text = "Uzgunum, ek kitap onerisi bulamadim. Lutfen farkli bir tur ya da yazari arayiniz."
    
    return context_text

def invoke_llm_with_retry(messages, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            if not rate_limiter.can_request():
                return "Su an cok yogunluk var. Lutfen biraz bekleyip tekrar deneyin."
            
            time.sleep(3)
            logger.info(f"Gemini API cagrisi yapiliyor (Deneme {attempt + 1})...")
            
            response = llm.invoke(messages)
            rate_limiter.record_request()
            return response.content
        
        except Exception as e:
            logger.error(f"API hatasi (Deneme {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(10 * (attempt + 1))
            else:
                return f"Hata: {str(e)}"

import difflib


def get_rag_response(question: str) -> str:
    question = sanitize_input(question)
    if not question:
        return "Bir soru sormaniz gerekli."
    
    rule_response = apply_rule_based_filter(question)
    if rule_response:
        return rule_response
    
    # AÇIKLAMALI FORMAT İLE QUERY OLUŞTUR
    formatted_query = extract_search_intent(question, chat_history)
    
    logger.info(f"Vektor aramasi yapiliyor (formatted)")
    query_vector = embed_text(formatted_query)
    similar_books = find_similar_books(query_vector, ALL_BOOKS, top_k=10)

    # YAZIM HATASINA DUYARLI YAZAR EŞLEŞTİRME 
    search_intent_raw = question.lower()
    clean_name = re.sub(r"(kitapları|kitabı|yazarı|eserleri|öner|bul|varmı|var mı)", "", search_intent_raw).strip()
    
    if len(clean_name) > 3:
        direct_matches = []
        # Veritabanındaki tüm benzersiz yazarları listeleyelim
        all_authors = list(set(b.get('author', '') for b in ALL_BOOKS))
        
        # Yazım hatalarını tolere et (Agatha Christine -> Agatha Christie)
        # cutoff=0.6 %60 benzerlik demektir, yeterli bir eşik.
        close_matches = difflib.get_close_matches(clean_name, [a.lower() for a in all_authors], n=1, cutoff=0.6)
        
        target_author = close_matches[0] if close_matches else None
        
        for b in ALL_BOOKS:
            author_name = b.get('author', '').lower()
            # Ya doğrudan dize içinde geçiyor mu ya da yakın eşleşme mi?
            if (clean_name in author_name) or (target_author and target_author == author_name):
                if not any(sb['id'] == b['id'] for sb in similar_books):
                    b_copy = b.copy()
                    b_copy['similarity'] = 0.99
                    direct_matches.append(b_copy)
        
        if direct_matches:
            logger.info(f"Yazar eşleşmesi (Yakın/Tam): {len(direct_matches)} kitap")
            similar_books = direct_matches + similar_books
            similar_books = similar_books[:12]
    # ==============================================================
    
    logger.info(f"Bulunan en yakin {len(similar_books)} kitap:")
    for i, b in enumerate(similar_books, 1):
        similarity_score = round(b.get('similarity', 0) * 100, 2)
        logger.info(f"   {i}. {b['title']} - {b['author']} (Benzerlik: %{similarity_score})")
    
    context_text = build_context_text(similar_books)
    
    try:
        messages = PROMPT_TEMPLATE.format_messages(
            context=context_text,
            question=question,
            chat_history=chat_history.messages
        )
        
        response_content = invoke_llm_with_retry(messages)
        
        chat_history.add_user_message(question)
        chat_history.add_ai_message(response_content)
        
        for book in similar_books[:3]:
            if not recommendation_tracker.is_already_recommended(book):
                recommendation_tracker.mark_recommended(book)
        
        return response_content
    
    except Exception as e:
        logger.error(f"RAG yanit olusturma hatasi: {e}")
        return f"Bir hata olustu: {str(e)}"

def start_chat():
    print("\n" + "="*60)
    print("BookMind Akilli Asistani Yayinda!")
    print("="*60)
    print("Ipuclari:")
    print("  * Yazarin adi soyleyiniz: 'Agatha Christie kitaplari var mi?'")
    print("  * Tur soyleyiniz: 'Bana polisiye kitap oner'")
    print("  * Cikmak icin 'q' yazin")
    print("="*60 + "\n")
    
    while True:
        user_input = input("\nSiz: ").strip()
        
        if not user_input or user_input.lower() == 'q':
            print("\nAsistan: Hosca kalin! Keyifli okumalar dilerim.")
            break
        
        response = get_rag_response(user_input)
        print(f"\nAsistan:\n{response}")

if __name__ == "__main__":
    start_chat()
