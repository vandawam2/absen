import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# --- KONFIGURASI WAJIB DIISI ---
URL_LOGIN = "https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F"
# Ganti dengan username (NRP/NIM) dan password Anda
USERNAME = "irvandawam@it.student.pens.ac.id"
PASSWORD = "Howto_321"
# URL halaman yang menampilkan semua kartu matkul (sesuai gambar)
URL_DAFTAR_KULIAH = "https://ethol.pens.ac.id/mahasiswa/matakuliah"
# Interval pengecekan (1800 detik = 30 menit)
INTERVAL_CEK = 2700

# --- PERBAIKAN 1: FUNGSI NOTIFIKASI YANG LEBIH ANDAL ---#

def notifikasi(pesan):
    """
    Fungsi notifikasi baru yang lebih andal.
    Menggunakan print yang menonjol dan bunyi 'beep' dari sistem.
    """
    print("\n" + "#"*60)
    print("###" + " "*54 + "###")
    # Membuat pesan menjadi uppercase dan ditengah
    pesan_tengah = pesan.upper().center(52)
    print(f"### {pesan_tengah} ###")
    print("###" + " "*54 + "###")
    print("#"*60 + "\n")
    # Mencetak karakter Bell (bunyi beep) untuk notifikasi suara
    try:
        for _ in range(5):
            print('\a', end='', flush=True)
            time.sleep(0.5)
    except Exception:
        pass # Abaikan jika gagal membunyikan suara

from webdriver_manager.chrome import ChromeDriverManager

# Pastikan Anda menggunakan metode manual untuk chromedriver
# Hapus 'from webdriver_manager.chrome import ChromeDriverManager'

def cek_semua_absen():
    # Menggunakan Service() kosong karena chromedriver.exe sudah di folder yang sama
    service = Service()
    options = webdriver.ChromeOptions()
    
    # --- TAMBAHKAN 4 BARIS INI ---
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage") # Penting untuk server Linux
    
    options.add_argument("--start-maximized") # Ini tetap penting
    
    # Setup service menggunakan webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    # Menaikkan waktu tunggu maksimal untuk mengantisipasi jaringan lambat
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

        # 5. Loop pengecekan utama
        while True:
            waktu_sekarang = time.strftime('%H:%M:%S')
            print(f"\n--- Memulai Pengecekan Siklus Baru pada {waktu_sekarang} ---")
            presensi_ditemukan = False

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
                    
                    # --- PERUBAHAN UTAMA: STRATEGI MENUNGGU YANG LEBIH STABIL ---
                    # Kita akan menunggu tombol "Aturan Presensi" yang lebih stabil untuk SIAP DIKLIK.
                    # Ini menandakan seluruh komponen presensi sudah selesai dimuat.
                    wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(span, 'Aturan Presensi')]")
                    ))
                    
                    time.sleep(1)

                    # Sekarang, setelah halaman dijamin stabil, baru lakukan pengecekan
                    tombol_presensi = driver.find_element(By.XPATH, "//button[normalize-space(span)='Presensi' and not(@disabled)]")
                    
                    tombol_presensi.click()
                    notifikasi(f"PRESENSI DIBUKA UNTUK MATKUL: {nama_matkul}")
                    
                    break

                except NoSuchElementException:
                    print(f"    Presensi untuk '{nama_matkul}' masih ditutup.")
                except Exception as e:
                    print(f"    Terjadi error saat mengecek '{nama_matkul}': {e}")

            if presensi_ditemukan:
                break
            
            print(f"\n--- Semua mata kuliah telah dicek. Siklus berikutnya dalam {INTERVAL_CEK / 60:.0f} menit. ---")
            time.sleep(INTERVAL_CEK)

    except TimeoutException:
        notifikasi("Error: Gagal login. Cek kembali USERNAME/PASSWORD Anda atau koneksi internet.")
    except Exception as e:
        notifikasi(f"Terjadi error yang tidak terduga: {e}")
    finally:
        print("Menutup browser...")
        driver.quit()        
                
if __name__ == "__main__":
    cek_semua_absen()

    print("Program selesai.")
