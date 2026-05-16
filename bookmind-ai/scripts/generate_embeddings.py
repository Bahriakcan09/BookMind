import os
import json
import sys

# Proje kök dizinini sys.path'e ekle (lib importu için)
# Betiğin bookmind-ai dizini içinden çalıştırılacağı varsayılmaktadır.
sys.path.append(os.getcwd())

try:
    from lib.embeddings import embed_text
except ImportError:
    # Eğer üst dizinden çalıştırılıyorsa
    sys.path.append(os.path.join(os.getcwd(), "bookmind-ai"))
    try:
        from lib.embeddings import embed_text
    except ImportError:
        print("Hata: lib.embeddings modülü bulunamadı. Lütfen betiği bookmind-ai dizini içinden çalıştırın.")
        sys.exit(1)

def generate():
    input_path = os.path.join('data', 'books_cleaned.json')
    output_path = os.path.join('data', 'books_with_embeddings.json')
    
    if not os.path.exists(input_path):
        print(f"Hata: {input_path} bulunamadı.")
        return

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        print(f"Hata: {input_path} dosyası okunurken hata oluştu: {e}")
        return

    total_books = len(books)
    processed_books = []
    
    print(f"Embedding oluşturma işlemi başlıyor ({total_books} kitap)...")

    for i, book in enumerate(books):
        try:
            # Metni birleştir: title author genre description
            title = book.get('title', '') or ''
            author = book.get('author', '') or ''
            genre = book.get('genre', '') or ''
            description = book.get('description', '') or ''
            
            text_to_embed = f"{title} {author} {genre} {description}"
            
            # Embedding oluştur
            book['embedding'] = embed_text(text_to_embed)
            processed_books.append(book)
            
            # İlerlemeyi göster
            if (i + 1) % 50 == 0 or (i + 1) == total_books:
                print(f"{i + 1}/{total_books} kitap işlendi...")
                
        except Exception as e:
            print(f"Hata: Kitap işlenirken bir sorun oluştu (ID: {book.get('id', 'Bilinmiyor')}): {e}")
            continue

    # Sonuçları kaydet
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_books, f, ensure_ascii=False, indent=2)
        print(f"İşlem tamamlandı. Veriler {output_path} dosyasına kaydedildi.")
    except Exception as e:
        print(f"Hata: {output_path} dosyasına yazılırken hata oluştu: {e}")

if __name__ == "__main__":
    generate()
