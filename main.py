# main.py - Versi Final dengan Opsi Isolasi Chrome
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, SessionNotCreatedException

# --- KONFIGURASI LOGGING ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- KONFIGURASI PENGGUNA ---
USERNAME = "irvandawam@it.student.pens.ac.id"
PASSWORD = "Howto_321"
URL_LOGIN = "https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F"
URL_DAFTAR_KULIAH = "https://ethol.pens.ac.id/mahasiswa/matakuliah"
INTERVAL_CEK = 2700

def cek_semua_absen():
    logging.info("Tahap 1: Menyiapkan opsi Chrome...")
    options = webdriver.ChromeOptions()
    options.binary_location = "/usr/bin/google-chrome"
    
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    # --- PERBAIKAN UTAMA DI SINI ---
    # Tambahkan argumen untuk isolasi yang lebih baik
    options.add_argument("--remote-debugging-port=0") # Gunakan port acak
    options.add_argument("--disable-extensions")      # Nonaktifkan ekstensi
    # Kita tidak secara eksplisit mengatur --user-data-dir, biarkan Selenium mengelola sementara

    driver = None
    try:
        logging.info("Tahap 2: Menginstal/menyiapkan chromedriver...")
        service = Service(ChromeDriverManager().install())

        logging.info("Tahap 3: Memulai instance browser Chrome...")
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Browser Chrome berhasil dimulai.")
        wait = WebDriverWait(driver, 120) # Tetap gunakan timeout 120 detik
        
        logging.info("Membuka halaman login CAS PENS...")
        driver.get(URL_LOGIN)
        logging.info("Memasukkan username dan password...")
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "submit").click()
        logging.info("Menunggu login berhasil...")
        wait.until(EC.url_contains("ethol.pens.ac.id/mahasiswa/beranda"))
        logging.info("Login berhasil! Kini berada di halaman Beranda.")
        time.sleep(2)

        logging.info("Mengklik tombol 'Matakuliah' di sidebar...")
        tombol_matakuliah = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='/mahasiswa/matakuliah']")
        ))
        tombol_matakuliah.click()
        
        logging.info("Menunggu halaman daftar kuliah termuat sepenuhnya...")
        wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
        ))
        logging.info("Halaman daftar kuliah berhasil dimuat!")

        logging.info("Mengambil daftar semua mata kuliah...")
        judul_matkul_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@class, 'card-title-mobile')]")
        ))
        nama_semua_matkul = [judul.text.strip() for judul in judul_matkul_elements if judul.text.strip()]
        
        if not nama_semua_matkul:
            logging.warning("Error: Tidak ada mata kuliah yang ditemukan.")
            return

        logging.info(f"Berhasil menemukan {len(nama_semua_matkul)} mata kuliah: {', '.join(nama_semua_matkul)}")

        for nama_matkul in nama_semua_matkul:
            logging.info(f"--> Mengecek matkul: {nama_matkul}")
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
                logging.warning(f"PRESENSI DIBUKA DAN DIKLIK UNTUK: {nama_matkul}")
                break

            except NoSuchElementException:
                logging.info(f"    Presensi untuk '{nama_matkul}' masih ditutup.")
            except Exception as e:
                logging.error(f"    Terjadi error saat mengecek '{nama_matkul}': {e}", exc_info=True)

    except SessionNotCreatedException as e:
        # Menangkap error spesifik ini untuk pesan yang lebih jelas
        logging.critical(f"Gagal memulai sesi Chrome: {e}", exc_info=True)
        logging.critical("Ini mungkin karena proses Chrome sebelumnya belum tertutup sepenuhnya. Coba deploy ulang.")
    except Exception as e:
        logging.critical(f"Terjadi error yang tidak terduga: {e}", exc_info=True)
    finally:
        if driver:
            logging.info("Menutup browser untuk siklus ini.")
            driver.quit()

if __name__ == '__main__':
    while True:
        logging.info(f"--- Memulai Pengecekan Siklus Baru ---")
        cek_semua_absen()
        logging.info(f"--- Siklus selesai. Siklus berikutnya dalam {INTERVAL_CEK / 60:.0f} menit. ---")
        time.sleep(INTERVAL_CEK)
