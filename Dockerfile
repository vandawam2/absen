# 1. Gunakan image dasar resmi Python
FROM python:3.11-slim

# 2. Instalasi dependensi sistem, termasuk Google Chrome
# Ini adalah bagian yang sebelumnya gagal
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    # Google Chrome itu sendiri
    google-chrome-stable \
    # Dependensi untuk headless Chrome
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    libasound2 \
    # Bersihkan cache untuk menjaga ukuran image tetap kecil
    && rm -rf /var/lib/apt/lists/*

# 3. Tetapkan direktori kerja di dalam container
WORKDIR /app

# 4. Salin file requirements dan instal library Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Salin semua file proyek Anda ke dalam container
COPY . .

# 6. Perintah yang akan dijalankan saat container dimulai
CMD ["python", "main.py"]
