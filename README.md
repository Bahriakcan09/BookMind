# BookMind - Web

Bu proje, bir Hackaton kapsamında geliştirilmiş, yemek tarifleri analizi ve market yönetimi sağlayan bir ASP.NET Core MVC uygulamasıdır. Gemini AI entegrasyonu ile tarifleri analiz eder ve Firebase kullanarak verileri depolar.

## 📂 Proje Yapısı

```text
Web/
├── HackatonProject/
│   ├── Controllers/          # Uygulama mantığını yöneten kontrolcüler
│   │   ├── AccountController    # Kullanıcı kayıt ve giriş işlemleri
│   │   ├── HomeController       # Ana sayfa ve genel sayfalar
│   │   ├── MarketController     # Ürün ve sepet yönetimi
│   │   ├── OrderController      # Sipariş ve takip işlemleri
│   │   └── RecipeController     # Yemek tarifi analizi (Gemini AI)
│   ├── Models/               # Veri modelleri (Product, Order, RecipeAnalysis vb.)
│   ├── Services/             # Harici servis entegrasyonları (Firebase, Gemini)
│   ├── Views/                # Arayüz dosyaları (Razor Pages)
│   ├── wwwroot/              # Statik dosyalar (CSS, JS, Resimler)
│   └── Program.cs            # Uygulama başlangıç noktası
└── HackatonProject.slnx      # Visual Studio Çözüm dosyası
```

## 🚀 Öne Çıkan Özellikler

- **Gemini AI Analizi:** Yemek tariflerini analiz ederek içerik ve besin değerleri hakkında bilgi sunar.
- **Market & Sepet Sistemi:** Ürünleri listeleyebilir, sepete ekleyebilir ve sipariş oluşturabilirsiniz.
- **Firebase Entegrasyonu:** Gerçek zamanlı veritabanı kullanımı.
- **Kullanıcı Yönetimi:** Kayıt olma ve giriş yapma özellikleri.

## 🛠️ Kurulum ve Çalıştırma

1. Depoyu klonlayın.
2. `Web/HackatonProject/appsettings.json` dosyasını oluşturun ve gerekli API anahtarlarını ekleyin.
3. Visual Studio veya .NET CLI kullanarak projeyi çalıştırın:
   ```bash
   dotnet run --project Web/HackatonProject
   ```

## 🔒 Güvenlik Notu
API anahtarları ve hassas veriler `.gitignore` dosyası ile korunmaktadır. Projeyi yayınlamadan önce kendi yapılandırmalarınızı kontrol etmeyi unutmayın.
