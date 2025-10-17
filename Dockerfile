# 1. Gunakan image dasar Python yang ramping
FROM python:3.11-slim

# 2. Instalasi dependensi dan Google Chrome dengan metode yang lebih efisien
# --no-install-recommends akan menghemat banyak ruang
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    # Hapus cache setelah setiap langkah untuk menjaga ukuran tetap kecil
    && rm -rf /var/lib/apt/lists/*

# 3. Tambahkan repositori Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# 4. Instal Google Chrome
RUN apt-get update && apt-get install -y --no-install-recommends \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 5. Tetapkan direktori kerja
WORKDIR /app

# 6. Salin dan instal library Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Salin sisa file proyek
COPY . .

# 8. Perintah untuk memulai skrip
CMD ["python", "main.py"]
