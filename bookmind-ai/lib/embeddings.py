# Bu modül, kitap açıklamalarını vektörlere dönüştürmek ve benzer kitapları bulmak için gerekli fonksiyonları içerir.
from sentence_transformers import SentenceTransformer
import numpy as np
import json

# Çok dilli (Multilingual) model: Türkçe ve diğer 50+ dili destekler.
# Anlamsal benzerlikte Türkçe cümleleri çok daha iyi anlar.
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def embed_text(text: str) -> list[float]:
    """Metni vektöre çevirir ve liste olarak döndürür."""
    embedding = model.encode(text)
    return embedding.tolist()

def cosine_similarity(vec1: list, vec2: list) -> float:
    """İki vektör arasındaki kosinüs benzerliğini hesaplar (0.0 - 1.0)."""
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    dot_product = np.dot(v1, v2)
    return float(dot_product / (norm_v1 * norm_v2))

def find_similar_books(query_vector: list, books: list, top_k: int = 5) -> list:
    """
    Books listesinde her kitabın embedding'i ile karşılaştırır.
    Benzerlik skoruna göre sıralar ve en yüksek top_k kitabı döndürür.
    """
    results = []
    for book in books:
        if book.get('embedding'):
            similarity = cosine_similarity(query_vector, book['embedding'])
            book_copy = book.copy()
            book_copy['similarity'] = similarity
            results.append(book_copy)
    
    # Benzerlik skoruna göre azalan sırada sırala
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:top_k]
