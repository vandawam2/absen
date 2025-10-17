import time
import os
import threading
from flask import Flask
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# --- KONFIGURASI PENGGUNA ---
# Pastikan username dan password Anda sudah benar
USERNAME = "irvandawam@it.student.pens.ac.id"
PASSWORD = "Howto_321"
URL_LOGIN = "https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F"
URL_DAFTAR_KULIAH = "https://ethol.pens.ac.id/mahasiswa/matakuliah"
INTERVAL_CEK = 2700  # Interval dalam detik (2700 detik = 45 menit)

# --- FUNGSI NOTIFIKASI (TIDAK PERLU DIUBAH) ---
def notifikasi(pesan):
    """Mencetak pesan notifikasi yang menonjol di log server."""
    print("\n" + "#"*60)
    pesan_tengah = pesan.upper().center(52)
    print(f"### {pesan_tengah} ###")
    print("#"*60 + "\n")

# --- FUNGSI UTAMA PENGECEKAN ABSEN ---
def cek_semua_absen():
    """Melakukan satu siklus penuh pengecekan absen untuk semua mata kuliah."""
    # Opsi driver untuk server Linux (Render)
    options = webdriver.ChromeOptions()
    # Memberitahu Selenium lokasi Chrome yang diinstal oleh buildpack Render
    options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    
    # Argumen wajib untuk mode headless (tanpa layar) di server
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    # Menginstal driver yang sesuai dan mengaturnya
    chrome_driver_path = ChromeDriverManager().install()
    service = Service(chrome_driver_path)
    
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 60)
    
    try:
        # 1. Proses Login
        print("Membuka halaman login CAS PENS...")
        driver.get(URL_LOGIN)
        print("Memasukkan username dan password...")
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "submit").click()
        print("Menunggu login berhasil...")
        wait.until(EC.url_contains("ethol.pens.ac.id/mahasiswa/beranda"))
        print("Login berhasil! Kini berada di halaman Beranda.")
        time.sleep(2)

        # 2. Navigasi ke Halaman Matakuliah
        print("Mengklik tombol 'Matakuliah' di sidebar...")
        tombol_matakuliah = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='/mahasiswa/matakuliah']")
        ))
        tombol_matakuliah.click()
        
        # 3. Tunggu Halaman Matakuliah Siap
        print("Menunggu halaman daftar kuliah termuat sepenuhnya...")
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
        ))
        print("Halaman daftar kuliah berhasil dimuat!")

        # 4. Ambil Daftar Mata Kuliah
        print("Mengambil daftar semua mata kuliah...")
        judul_matkul_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@class, 'card-title-mobile')]")
        ))
        nama_semua_matkul = [judul.text.strip() for judul in judul_matkul_elements if judul.text.strip()]
        
        if not nama_semua_matkul:
            notifikasi("Error: Tidak ada mata kuliah yang ditemukan.")
            return

        print(f"Berhasil menemukan {len(nama_semua_matkul)} mata kuliah: {', '.join(nama_semua_matkul)}")

        # 5. Loop Pengecekan Setiap Mata Kuliah
        for nama_matkul in nama_semua_matkul:
            print(f"--> Mengecek matkul: {nama_matkul}")
            try:
                # Kembali ke halaman daftar matkul jika perlu
                if "/mahasiswa/matakuliah" not in driver.current_url:
                    driver.get(URL_DAFTAR_KULIAH)
                    wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
                    ))
                
                # Klik "Akses Kuliah"
                tombol_akses = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[contains(@class, 'card-matkul') and .//span[normalize-space()='{nama_matkul}']]//button[contains(., 'Akses Kuliah')]")
                ))
                driver.execute_script("arguments[0].click();", tombol_akses)
                
                # Tunggu halaman detail stabil
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space(span)='Aturan Presensi']")
                ))
                time.sleep(1) # Jeda singkat untuk verifikasi akhir

                # Cari dan klik tombol presensi yang aktif
                tombol_presensi = driver.find_element(By.XPATH, "//button[normalize-space(span)='Presensi' and not(@disabled)]")
                tombol_presensi.click()
                notifikasi(f"PRESENSI DIBUKA DAN DIKLIK UNTUK: {nama_matkul}")
                break

            except NoSuchElementException:
                print(f"    Presensi untuk '{nama_matkul}' masih ditutup.")
            except Exception as e:
                print(f"    Terjadi error saat mengecek '{nama_matkul}': {e}")

    except TimeoutException:
        notifikasi("Error: Gagal login. Cek kembali USERNAME/PASSWORD atau koneksi internet.")
    except Exception as e:
        notifikasi(f"Terjadi error yang tidak terduga: {e}")
    finally:
        print("Menutup browser untuk siklus ini.")
        driver.quit()

# --- BAGIAN SERVER WEB UNTUK RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    """Halaman web sederhana untuk menjaga layanan tetap aktif."""
    return "Bot Absen Aktif. Pengecekan berjalan di latar belakang."

def run_absen_loop():
    """Fungsi yang menjalankan siklus pengecekan berulang kali selamanya."""
    while True:
        waktu_sekarang = time.strftime('%H:%M:%S')
        print(f"\n--- Memulai Pengecekan Siklus Baru pada {waktu_sekarang} ---")
        
        cek_semua_absen()
        
        print(f"--- Siklus selesai. Siklus berikutnya dalam {INTERVAL_CEK / 60:.0f} menit. ---")
        time.sleep(INTERVAL_CEK)

if __name__ == '__main__':
    # Menjalankan loop absen di "jalur" terpisah (thread)
    print("Memulai thread bot absen di latar belakang...")
    absen_thread = threading.Thread(target=run_absen_loop)
    absen_thread.daemon = True
    absen_thread.start()
    
    # Menjalankan server web Flask
    print("Memulai web server Flask...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
