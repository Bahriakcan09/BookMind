# Hafif Python imajı
FROM python:3.10-slim

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıkları (Kullanıcı izinleri için gerekli araçlar dahil)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Hugging Face için 'user' (UID 1000) oluşturma
RUN useradd -m -u 1000 user

# Bağımlılıkları kopyala ve kur
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala ve sahipliğini 'user'a ver
COPY --chown=user:user . .

# Hugging Face varsayılan portu
ENV PORT=7860

# Kullanıcıyı değiştir (Güvenlik ve HF standardı)
USER user

# Sunucuyu başlat
CMD ["sh", "-c", "uvicorn app.prod_main:app --host 0.0.0.0 --port $PORT"]
