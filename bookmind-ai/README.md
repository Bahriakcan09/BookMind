# 🧠 BookMind AI: Teknik Dokümantasyon ve Mimari Derinlik

BookMind AI, klasik bir chatbot'un ötesinde, **Retrieval-Augmented Generation (RAG)** tabanlı, kişiselleştirilmiş bir kitap danışmanlık sistemidir. Bu doküman, sistemin veriden bilgiye, bilgiden kişiselleştirilmiş öneriye dönüşüm sürecini teknik detaylarıyla açıklar.

---

## 🏛️ Mimari Derinlik

Sistemimiz dört temel katmandan oluşur: **Veri İşleme (ETL)**, **Anlamsal Arama (Retrieval)**, **Veritabanı (Context Manager)** ve **Üretim (Generation)**.

### 1. Veri İşleme Hattı (ETL Pipeline)
Ham verinin (Google Books API) anlamlı bir vektör uzayına dönüştürülmesi süreci:

*   **Extraction (`fetch_books.py`):** Google Books API üzerinden kitap meta-verileri (başlık, yazar, kategori, açıklama) JSON formatında çekilir.
*   **Transformation (`clean_data.py`):** 
    *   **Normalizasyon:** HTML etiketleri temizlenir, Türkçe karakter kodlaması standartlaştırılır.
    *   **Filtreleme:** Eksik açıklamalı veya geçersiz formatlı kitaplar elenir.
    *   **ID Mapping:** Firebase/Firestore ile uyumlu, benzersiz doküman ID'leri atanır.
*   **Loading/Vectorization (`generate_embeddings.py`):** Kitap açıklamaları `Sentence-Transformers` veya benzeri bir model ile (384/768 boyutlu) vektör uzayına map edilir. Bu vektörler, arama sırasında hızlı kosinüs benzerliği hesabı için `books_cleaned.json` içinde "indexed" olarak saklanır.

### 2. RAG ve Arama Mimarisi (Retrieval)
Kullanıcı bir soru sorduğunda (örneğin: "Polisiye önerir misin?"):

1.  **Sorgu Vektörleştirme:** Kullanıcının mesajı, kitap veritabanı ile aynı embedding modeli kullanılarak vektöre dönüştürülür.
2.  **Kosinüs Benzerliği:** Sorgu vektörü, kitap vektör uzayındaki tüm kitaplarla karşılaştırılır (`embeddings.py` içerisindeki algoritma ile). En yüksek benzerliğe (Top-K) sahip 3-5 kitap "bağlam" olarak seçilir.
3.  **Kişiselleştirme (Firebase Context):** `firebase_db.py` üzerinden kullanıcının `libraries` (okuduğu kitaplar) ve `carts` (sepeti) verileri çekilir. Bu, modelin "kullanıcı daha önce okumuş olabilir" veya "bu türe ilgi duyuyor" çıkarımı yapmasını sağlar.

### 3. LLM ve Prompt Mühendisliği (`chatbot.py`)
Gemini'ye gönderilen nihai "Prompt", dinamik olarak inşa edilir:

```text
[SİSTEM ROLÜ]: Sen uzman bir kitap danışmanısın.
[BAĞLAM (RAG)]: Veritabanından bulunan en alakalı kitaplar: {retrieved_books}
[KULLANICI PROFİLİ]: Kullanıcının okuma geçmişi ve tercihleri: {user_profile}
[GÖREV]: Kullanıcıya, bağlamdaki kitapları kullanarak, kişiselleştirilmiş ve ikna edici bir öneri sun. 
Eğer kullanıcı daha önce okumuşsa, o kitabı önerme.
[KULLANICI SORUSU]: {user_message}
```

### 4. Veritabanı Yapısı (Firestore)
Firebase, hem sistemin veri hafızası hem de kullanıcı bağlamının merkezidir.

*   **`books` Koleksiyonu:** Kitap meta-verilerinin (yazar, tür, ISBN, description) saklandığı dokümanlar.
*   **`users` Koleksiyonu:** 
    *   `history`: Okunan kitap ID'leri.
    *   `preferences`: Sevilen kategoriler/yazarlar.
    *   `carts`: Sepete eklenen kitaplar.

---

## 📂 Klasör Yapısı

```text
bookmind-ai/
├── app/
│   ├── main.py               # FastAPI: Uç noktalar, CORS ve Request validation.
│   └── service/
│       └── chatbot.py        # Zeka Merkezi: Prompt construction, RAG akışı, API entegrasyonu.
├── data/                     # Data Lake:
│   ├── books.json            # Ham ham API çıktısı.
│   └── books_cleaned.json    # Vektörleri de içeren işlenmiş veritabanı.
├── lib/
│   ├── embeddings.py         # AI Modülleri: Vektörleştirme ve Kosinüs benzerliği.
│   └── firebase_db.py        # Veri Köprüsü: Firestore CRUD operasyonları.
├── scripts/                  # Data Pipeline (ETL):
│   ├── fetch_books.py        # Veri toplama betiği.
│   ├── clean_data.py         # Temizleme ve ID re-indexing.
│   └── generate_embeddings.py # Vektör uzayı oluşturucu.
└── .env                      # Ortam değişkenleri (Gemini Key, Firebase Config).
```

---

## 🚀 Çalıştırma ve Kurulum

1.  **Gereksinimler:** `pip install -r requirements.txt` (HuggingFace transformers, firebase-admin, fastapi, uvicorn).
2.  **Yapılandırma:**
    *   `.env` dosyasına `GOOGLE_API_KEY` ekleyin.
    *   `firebase-key.json` dosyasını kök dizine koyun.
3.  **Pipeline Başlatma:** `scripts/` altındaki dosyaları `fetch` -> `clean` -> `generate_embeddings` sırasıyla çalıştırarak veritabanını hazırlayın.
4.  **API:** `python app/main.py` ile sunucuyu başlatın.

---

## 🌐 Canlı Demo
BookMind AI projesi yayındadır! Canlı çalışan sistemi incelemek ve kod yapısını görmek için aşağıdaki bağlantıyı ziyaret edebilirsiniz:

👉 **[Canlı Demo ve Kaynak Kodları (Hugging Face Spaces)](https://huggingface.co/spaces/DemetAsgaroglu/bookmind-ai/tree/main)**

---
*BookMind AI, 2026 Hackathon için geliştirilmiştir.*
