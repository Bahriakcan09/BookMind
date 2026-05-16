import json
import os
import sys

# Proje kök dizinini sys.path'e ekle
sys.path.append(os.getcwd())

from lib.embeddings import embed_text, find_similar_books

def test_search():
    embeddings_file = os.path.join('data', 'books_with_embeddings.json')
    
    if not os.path.exists(embeddings_file):
        print(f"Hata: {embeddings_file} bulunamadı. Önce generate_embeddings.py çalıştırmalısınız.")
        return

    print("--- BookMind Benzerlik Test Sistemi ---")
    
    # Veriyi yükle
    with open(embeddings_file, 'r', encoding='utf-8') as f:
        books = json.load(f)
    
    while True:
        print("\n" + "="*50)
        query = input("Aramak istediğiniz konuyu yazın (Çıkmak için 'q'): ")
        
        if query.lower() == 'q':
            break
            
        print(f"'{query}' için arama yapılıyor...")
        
        # Sorguyu vektöre çevir
        query_vector = embed_text(query)
        
        # En yakın 5 kitabı bul
        results = find_similar_books(query_vector, books, top_k=5)
        
        print("\nEn Yakın Sonuçlar:")
        for i, res in enumerate(results, 1):
            title = res.get('title', 'Bilinmiyor')
            author = res.get('author', 'Bilinmiyor')
            genre = res.get('genre', 'Bilinmiyor')
            score = res.get('similarity', 0)
            desc = res.get('description', '')[:150] + "..."
            
            print(f"{i}. [{round(score * 100, 2)}%] {title} - {author} ({genre})")
            print(f"   Özet: {desc}")
            print("-" * 30)

if __name__ == "__main__":
    test_search()
