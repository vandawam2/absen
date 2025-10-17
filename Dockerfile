# 1. Gunakan image dasar resmi Python
FROM python:3.11-slim

# 2. Tambahkan repositori Google Chrome dan instal software yang dibutuhkan
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    # Sekarang sistem tahu di mana harus mencari google-chrome-stable
    && apt-get install -y google-chrome-stable \
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
