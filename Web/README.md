# BookMind - Geleceğin Dijital Kütüphanesi

BookMind, kitap tutkunları için tasarlanmış, yapay zeka destekli, modern bir dijital kütüphane ve alışveriş platformudur. Bu proje, fiziksel kitaplarınızı dijital kütüphanenize taşımanıza, yeni kitaplar keşfetmenize ve akıllı asistanınızla kitaplar üzerine sohbet etmenize olanak tanır.

## 🚀 Temel Özellikler

### 1. Akıllı Kitap Keşfi ve Firestore Entegrasyonu
- **Dinamik Listeleme:** Tüm kitap verileri **Google Firebase Firestore** üzerinden çekilir.
- **Performans Odaklı:** Büyük boyutlu `embedding` verileri çekilmeden, sadece ihtiyaç duyulan bilgiler asenkron olarak yüklenir.
- **Sayfalama (Pagination):** Her sayfada 20 kitap olacak şekilde, gelişmiş navigasyon (ilk/son/ileri/geri) desteğiyle listeleme yapılır.
- **Kategori Filtreleme:** Kitap türlerine göre (Polisiye, Macera vb.) anlık filtreleme ve alfabetik sıralama.
- **Arama:** Kitap adı veya yazara göre gerçek zamanlı arama motoru.

### 2. Gelişmiş Sepet ve Sipariş Sistemi
- **Çift Taraflı Senkronizasyon:** Sepet verileri hem `localStorage` hem de giriş yapıldığında **Firebase Realtime Database** üzerinde tutulur.
- **Anlık Güncelleme:** Veritabanındaki değişiklikler tüm cihazlarda anlık olarak (Real-time listener) arayüze yansır.
- **Sipariş Geçmişi:** Ödeme simülasyonu sonrası siparişler `orders/{uid}` altında arşivlenir ve kullanıcı profilinde listelenir.

### 3. Dijital Kütüphanem ve Barkod/ISBN Tarayıcı
- **Barkod Okuma:** `html5-qrcode` kütüphanesi ile kamera üzerinden veya cihazdan fotoğraf yükleyerek barkod/ISBN tarama.
- **Google Books Entegrasyonu:** Taranan ISBN üzerinden kitap detayları (kapak, yazar, tür) otomatik olarak Google Books API üzerinden çekilir.
- **Otomatik Kütüphane Kaydı:** Satın alınan her kitap, kütüphaneye otomatik olarak eklenir.
- **Manuel Kayıt:** Barkodu okunamayan veya API'da bulunmayan kitaplar için manuel veri girişi desteği.

### 4. AI Chatbot (Hugging Face & FastAPI)
- **Gerçek Zamanlı Sohbet:** Hugging Face Spaces üzerinde barındırılan **FastAPI** tabanlı AI modeline bağlıdır.
- **RAG Altyapısı:** Yapay zeka, kütüphanedeki gerçek verileri kullanarak akıllı kitap önerileri sunar.
- **Oturum Koruması:** `sessionStorage` sayesinde sayfa geçişlerinde mesaj geçmişi korunur, tarayıcı kapandığında temizlenir.

### 5. Modern ve Dinamik Tasarım
- **Glassmorphism:** Yarı şeffaf navbar ve modern görsel efektler.
- **Responsive:** Mobil ve masaüstü cihazlarla tam uyumlu.
- **Hover Efektleri:** Dinamik ve yaşayan bir arayüz hissi için yumuşak geçişler ve animasyonlar.

---

## 🛠 Kullanılan Teknolojiler
- **Backend:** ASP.NET Core 10.0 (MVC), FastAPI (Python - AI Service)
- **Frontend:** HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3
- **Veritabanı:** Google Firebase Firestore, Firebase Realtime Database
- **Kimlik Doğrulama:** Firebase Authentication
- **AI/ML:** Hugging Face Spaces, RAG (Retrieval-Augmented Generation)

---

## 📁 Proje Dizin Yapısı
```text
BookMind/
├── Controllers/         # İş mantığını yöneten Controller sınıfları
│   ├── AuthController.cs
│   ├── CartController.cs
│   ├── HomeController.cs
│   └── LibraryController.cs
├── Views/               # Arayüz dosyaları (.cshtml)
│   ├── Auth/            # Giriş ve Kayıt sayfaları
│   ├── Cart/            # Sepet, Ödeme ve Siparişlerim sayfaları
│   ├── Home/            # Ana sayfa ve Kitap Detayları
│   ├── Library/         # Kütüphanem (Barkod Tarayıcı) sayfası
│   └── Shared/          # Ortak şablonlar (Layout, Chatbot, Navbar)
├── wwwroot/             # Statik dosyalar
│   ├── css/             # Modernize edilmiş site.css
│   ├── js/              # Firebase, Cart, AI ve UI mantığını yöneten scriptler
│   └── lib/             # Üçüncü taraf kütüphaneler (Bootstrap, jQuery)
└── README.md            # Proje dökümantasyonu
```

---

## ⚙️ Kurulum ve Çalıştırma
1. Projeyi bilgisayarınıza indirin veya klonlayın.
2. `firebase-config.js` dosyasındaki Firebase ayarlarının kendi projenize uygun olduğunu kontrol edin.
3. Visual Studio 2022 veya VS Code üzerinden projeyi açın.
4. `dotnet run` komutuyla veya Visual Studio üzerinden projeyi başlatın.
5. Uygulama varsayılan olarak `https://localhost:7238` üzerinden erişilebilir olacaktır.

---
*Bu proje bir Hackathon çalışması olarak geliştirilmiştir.*
