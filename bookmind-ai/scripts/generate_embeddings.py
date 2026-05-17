import os
import json
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.getcwd())

try:
    from lib.embeddings import embed_text
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), "bookmind-ai"))
    try:
        from lib.embeddings import embed_text
    except ImportError:
        logger.error("Hata: lib.embeddings modülü bulunamadı.")
        sys.exit(1)

def generate_embeddings(
    input_path: str = 'data/books_cleaned.json',
    output_path: str = 'data/books_with_embeddings.json'
) -> dict:
    """
    JSON'dan embedding oluştur ve kaydet.

    """
    
    if not os.path.exists(input_path):
        logger.error(f"Dosya bulunamadı: {input_path}")
        return {'success': False}
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
    except Exception as e:
        logger.error(f"JSON okuma hatası: {e}")
        return {'success': False}
    
    total_books = len(books)
    processed_books = []
    failed_books = []
    
    logger.info(f"Embedding oluşturma başlıyor ({total_books} kitap)...")
    logger.info("=" * 70)
    
    for i, book in enumerate(books):
        try:
            # AÇIKLAMALI FORMAT (JSON'daki gibi)
            title = book.get('title', 'Bilinmiyor')
            author = book.get('author', 'Bilinmeyen Yazar')
            genre = book.get('genre', 'Genel')
            description = book.get('description', '')
            
            # ÖNEMLİ: AYNI FORMAT!
            text_to_embed = (
                f"KİTAP ADI: {title}\n"
                f"YAZAR: {author}\n"
                f"TÜR: {genre}\n"
                f"ÖZET: {description}"
            )
            
            # Embedding oluştur
            embedding = embed_text(text_to_embed)
            book['embedding'] = embedding
            processed_books.append(book)
            
            # İlerleme
            if (i + 1) % 50 == 0 or (i + 1) == total_books:
                logger.info(f"[{i + 1:4d}/{total_books:4d}] işlendi")
        
        except Exception as e:
            logger.warning(f"Kitap {i+1} başarısız: {e}")
            failed_books.append({'index': i + 1, 'title': book.get('title')})
            continue
    
    # Dosyaya kaydet
    logger.info("=" * 70)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_books, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✓ İşlem tamamlandı!")
        logger.info(f"  Başarılı: {len(processed_books)} kitap")
        logger.info(f"  Başarısız: {len(failed_books)} kitap")
        logger.info(f"  Dosya: {output_path}")
        
        return {'success': True, 'processed': len(processed_books)}
    
    except Exception as e:
        logger.error(f"Dosya yazma hatası: {e}")
        return {'success': False}

if __name__ == "__main__":
    result = generate_embeddings()
    
    if result['success']:
        logger.info("\n Embedding oluşturma başarılı!")
        sys.exit(0)
    else:
        logger.error("\n Embedding oluşturma başarısız!")
        sys.exit(1)
