import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from flask import Flask
import threading

# --- KONFIGURASI WAJIB DIISI ---
USERNAME = "irvandawam@it.student.pens.ac.id"
PASSWORD = "Howto_321"
URL_LOGIN = "https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F"
URL_DAFTAR_KULIAH = "https://ethol.pens.ac.id/mahasiswa/matakuliah"
INTERVAL_CEK = 2700

# --- FUNGSI NOTIFIKASI (TIDAK BERUBAH) ---
def notifikasi(pesan):
    print("\n" + "#"*60)
    print("###" + " "*54 + "###")
    pesan_tengah = pesan.upper().center(52)
    print(f"### {pesan_tengah} ###")
    print("###" + " "*54 + "###")
    print("#"*60 + "\n")
    try:
        for _ in range(5):
            print('\a', end='', flush=True)
            time.sleep(0.5)
    except Exception:
        pass

# --- FUNGSI UTAMA PENGECEKAN ABSEN (TIDAK BERUBAH) ---
def cek_semua_absen():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 60)
    
    presensi_ditemukan_di_siklus_ini = False
    try:
        # 1. Proses Login
        print("Membuka halaman login CAS PENS...")
        driver.get(URL_LOGIN)
        # ... (Sisa logika login dan pengecekan Anda tetap sama persis)
        print("Memasukkan username dan password...")
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "submit").click()
        print("Menunggu login berhasil...")
        wait.until(EC.url_contains("ethol.pens.ac.id/mahasiswa/beranda"))
        print("Login berhasil! Kini berada di halaman Beranda.")
        time.sleep(2)

        # 2. Klik Tombol "Matakuliah" di Sidebar
        print("Mengklik tombol 'Matakuliah' di sidebar...")
        tombol_matakuliah = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='/mahasiswa/matakuliah']")
        ))
        tombol_matakuliah.click()
        
        # 3. Tunggu Konfirmasi Halaman Matakuliah
        print("Menunggu halaman daftar kuliah termuat sepenuhnya...")
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
        ))
        print("Halaman daftar kuliah berhasil dimuat!")

        # 4. Ambil semua nama mata kuliah
        print("Mengambil daftar semua mata kuliah...")
        judul_matkul_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@class, 'card-title-mobile')]")
        ))
        nama_semua_matkul = [judul.text.strip() for judul in judul_matkul_elements if judul.text.strip()]
        
        if not nama_semua_matkul:
            notifikasi("Error: Tidak ada mata kuliah yang ditemukan.")
            return

        print(f"Berhasil menemukan {len(nama_semua_matkul)} mata kuliah: {', '.join(nama_semua_matkul)}")

        # 5. Loop pengecekan untuk setiap mata kuliah
        for nama_matkul in nama_semua_matkul:
            print(f"--> Mengecek matkul: {nama_matkul}")
            try:
                if "/mahasiswa/matakuliah" not in driver.current_url:
                    driver.get(URL_DAFTAR_KULIAH)
                    wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
                    ))
                
                tombol_akses = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[contains(@class, 'card-matkul') and .//span[normalize-space()='{nama_matkul}']]//button[contains(., 'Akses Kuliah')]")
                ))
                driver.execute_script("arguments[0].click();", tombol_akses)
                
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space(span)='Aturan Presensi']")
                ))
                time.sleep(1)

                tombol_presensi = driver.find_element(By.XPATH, "//button[normalize-space(span)='Presensi' and not(@disabled)]")
                
                tombol_presensi.click()
                notifikasi(f"PRESENSI DIBUKA DAN DIKLIK UNTUK: {nama_matkul}")
                presensi_ditemukan_di_siklus_ini = True
                break # Hentikan pengecekan matkul lain di siklus ini

            except NoSuchElementException:
                print(f"    Presensi untuk '{nama_matkul}' masih ditutup.")
            except Exception as e:
                print(f"    Terjadi error saat mengecek '{nama_matkul}': {e}")

    except TimeoutException:
        notifikasi("Error: Gagal login. Cek kembali USERNAME/PASSWORD Anda atau koneksi internet.")
    except Exception as e:
        notifikasi(f"Terjadi error yang tidak terduga: {e}")
    finally:
        print("Menutup browser untuk siklus ini.")
        driver.quit()

# --- BAGIAN BARU UNTUK MENJALANKAN DI RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Absen Aktif. Pengecekan berjalan di latar belakang."

# --- PERUBAHAN UTAMA DI SINI ---
def run_absen_loop():
    # Fungsi ini sekarang akan berjalan selamanya tanpa henti
    while True:
        waktu_sekarang = time.strftime('%H:%M:%S')
        print(f"\n--- Memulai Pengecekan Siklus Baru pada {waktu_sekarang} ---")
        
        # Cukup jalankan fungsi pengecekan
        cek_semua_absen()
        
        # Setelah selesai (berhasil atau tidak), selalu tunggu untuk siklus berikutnya
        print(f"--- Siklus selesai. Siklus berikutnya dalam {INTERVAL_CEK / 60:.0f} menit. ---")
        time.sleep(INTERVAL_CEK)

if __name__ == '__main__':
    print("Memulai thread bot absen di latar belakang...")
    absen_thread = threading.Thread(target=run_absen_loop)
    absen_thread.start()
    
    print("Memulai web server Flask...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
