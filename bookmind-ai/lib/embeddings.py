"""
BookMind Embedding Modülü
========================

Kitap açıklamalarını vektörlere dönüştürmek ve benzer kitapları bulmak için
gerekli fonksiyonları içerir.

Agatha Christie sorunu çözüldü:
- Robust vektör boyutu kontrolü
- NaN/Inf değer kontrolü
- Detaylı error handling
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import logging

# Logging ayarla (Sadece bu modül için)
logger = logging.getLogger(__name__)

# Çok dilli (Multilingual) model: Türkçe ve diğer 50+ dili destekler.
# Anlamsal benzerlikte Türkçe cümleleri çok daha iyi anlar.
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def embed_text(text: str) -> list:
    """
    Metni vektöre çevirir ve liste olarak döndürür.
    
    Args:
        text: Embedding'e dönüştürülecek metin
        
    Returns:
        384 boyutlu float listesi
    """
    embedding = model.encode(text)
    return embedding.tolist()

def cosine_similarity(vec1: list, vec2: list) -> float:
    """
    İki vektör arasındaki kosinüs benzerliğini hesaplar (0.0 - 1.0).
    
    Geliştirildi:
    - Vektör boyutu uyuşması kontrol
    - NaN/Inf değer kontrolü
    - Zero vector kontrolü
    
    Args:
        vec1: Birinci vektör
        vec2: İkinci vektör
        
    Returns:
        0.0 ile 1.0 arasında benzerlik
        
    Raises:
        ValueError: Vektörler uyumsuzsa
    """
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    
    # Vektör boyutu kontrolü (KRİTİK!)
    if len(v1) != len(v2):
        raise ValueError(f"Vektör boyutları uyuşmıyor: {len(v1)} vs {len(v2)}")
    
    # NaN/Inf kontrol
    if np.any(np.isnan(v1)) or np.any(np.isinf(v1)):
        logger.warning("Query vektöründe NaN/Inf tespit edildi")
        return 0.0
    
    if np.any(np.isnan(v2)) or np.any(np.isinf(v2)):
        logger.warning("Book vektöründe NaN/Inf tespit edildi")
        return 0.0
    
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    # Zero vector kontrolü
    if norm_v1 == 0 or norm_v2 == 0:
        logger.warning("Zero vector tespit edildi")
        return 0.0
    
    dot_product = np.dot(v1, v2)
    return float(dot_product / (norm_v1 * norm_v2))

def find_similar_books(query_vector: list, books: list, top_k: int = 10) -> list:
    """
    Books listesinde her kitabın embedding'i ile karşılaştırır.
    Benzerlik skoruna göre sıralar ve en yüksek top_k kitabı döndürür.
    
    DÜZELTMELER:
    1. Vektör boyutu uyuşması kontrol et (KRİTİK!)
    2. NaN/Inf değerleri kontrol et
    3. Hataları gracefully handle et
    4. Debug bilgisi logla
    5. top_k=10 default (daha fazla sonuç)
    
    Args:
        query_vector: Query embedding'i (384 boyut)
        books: Kitap listesi (her kitabın 'embedding' alanı olmalı)
        top_k: Döndürülecek sonuç sayısı (default: 10)
        
    Returns:
        Benzerlik skoruna göre sıralanmış kitap listesi
    """
    results = []
    
    if not query_vector:
        logger.error("Query vector boş!")
        return []
    
    query_dim = len(query_vector)
    logger.debug(f"Query boyutu: {query_dim}")
    
    # İstatistikler
    total_books = len(books)
    books_with_embedding = 0
    books_processed = 0
    books_skipped = 0
    dimension_mismatch = 0
    
    for idx, book in enumerate(books):
        # 1. Embedding alanı var mı?
        if not book.get('embedding'):
            books_skipped += 1
            continue
        
        books_with_embedding += 1
        book_embedding = book['embedding']
        book_title = book.get('title', 'Unknown')
        
        try:
            # 2. Embedding'i numpy array'e dönüştür
            if isinstance(book_embedding, list):
                book_vec = np.array(book_embedding, dtype=np.float32)
            elif isinstance(book_embedding, np.ndarray):
                book_vec = book_embedding
            else:
                logger.debug(f"[{book_title}] Bilinmeyen embedding tipi")
                books_skipped += 1
                continue
            
            # 3. ANAHTAR: Vektör boyutu uyuşuyor mu?
            if len(book_vec) != query_dim:
                logger.debug(
                    f"[{book_title}] Boyut uyuşmazlığı: "
                    f"query={query_dim}, book={len(book_vec)}"
                )
                dimension_mismatch += 1
                books_skipped += 1
                continue
            
            # 4. Geçerli vektör mü?
            if np.any(np.isnan(book_vec)) or np.any(np.isinf(book_vec)):
                logger.debug(f"[{book_title}] Geçersiz embedding (NaN/Inf)")
                books_skipped += 1
                continue
            
            # 5. Benzerlik hesapla
            try:
                similarity = cosine_similarity(query_vector, book_embedding)
            except ValueError as e:
                logger.debug(f"[{book_title}] Benzerlik hatası: {e}")
                books_skipped += 1
                continue
            
            # 6. Geçerli benzerlik mi?
            if np.isnan(similarity) or np.isinf(similarity):
                logger.debug(f"[{book_title}] Geçersiz benzerlik")
                books_skipped += 1
                continue
            
            # 7. Sonuca ekle
            book_copy = book.copy()
            book_copy['similarity'] = float(similarity)
            results.append(book_copy)
            books_processed += 1
            
        except Exception as e:
            logger.error(f"[{book_title}] Beklenmeyen hata: {e}")
            books_skipped += 1
            continue
    
    # Benzerlik skoruna göre azalan sırada sırala
    results.sort(key=lambda x: x['similarity'], reverse=True)
    
    # Debug logging
    logger.debug(
        f"Arama istatistikleri: "
        f"toplam={total_books}, "
        f"embedding_var={books_with_embedding}, "
        f"işlendi={books_processed}, "
        f"boyut_hatası={dimension_mismatch}, "
        f"sonuç={len(results)}"
    )
    
    # Top-K döndür
    return results[:top_k]
