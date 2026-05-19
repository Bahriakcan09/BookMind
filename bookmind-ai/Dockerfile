# Hafif Python imajı kullanıyoruz
FROM python:3.10-slim

# Çalışma dizinini oluştur
WORKDIR /app

# Sistem bağımlılıklarını kur (Bazı kütüphaneler için gerekebilir)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılık dosyasını kopyala ve kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Tüm proje dosyalarını kopyala
COPY . .

# Render.com'un dinamik portuna uyum sağlamak için ortam değişkeni
ENV PORT=8000

# Sunucuyu başlat (Prod main üzerinden)
CMD ["sh", "-c", "uvicorn app.prod_main:app --host 0.0.0.0 --port $PORT"]
