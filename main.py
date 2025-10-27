# main.py - Versi Final dengan Peningkatan Stabilitas Headless
import time
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# Hapus 'ChromeDriverManager' karena kita akan mengandalkan buildpack
# from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, SessionNotCreatedException, WebDriverException

# --- KONFIGURASI LOGGING ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- KONFIGURASI PENGGUNA ---
# PENTING: Ganti dengan kredensial Anda yang sebenarnya
USERNAME = "irvandawam@it.student.pens.ac.id" 
PASSWORD = "Howto_321" 
URL_LOGIN = "https://login.pens.ac.id/cas/login?service=http%3A%2F%2Fethol.pens.ac.id%2Fcas%2F"
URL_DAFTAR_KULIAH = "https://ethol.pens.ac.id/mahasiswa/matakuliah"
# Interval pengecekan (2700 detik = 45 menit)
INTERVAL_CEK = 2700 

def cek_semua_absen():
    logging.info("Tahap 1: Menyiapkan opsi Chrome...")
    options = webdriver.ChromeOptions()
    
    # Lokasi binary Chrome (sesuai dengan konfigurasi Linux container umum)
    options.binary_location = "/usr/bin/google-chrome"
    
    # Opsi dasar untuk mode Headless
    options.add_argument("--headless=new") # Eksplisit menggunakan mode headless baru
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # --- PERBAIKAN STABILITAS UTAMA UNTUK MENGATASI STATUS CODE -5 ---
    # 1. Nonaktifkan Sandbox: Penting di lingkungan Linux yang terisolasi/container
    options.add_argument("--no-sandbox") 
    # 2. Nonaktifkan Penggunaan Shared Memory: Untuk mengatasi batasan /dev/shm
    options.add_argument("--disable-dev-shm-usage") 
    # 3. Nonaktifkan Fitur yang rawan crash di headless/lingkungan terbatas
    options.add_argument("--disable-extensions") 
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-features=RendererCodeIntegrity")
    options.add_argument("--disable-browser-side-navigation") # Kadang membantu mencegah crash
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized") # Memastikan jendela selalu maksimal
    options.add_argument("--remote-debugging-port=0")
    
    # Opsi tambahan untuk menenangkan logging dan startup
    options.add_argument("--log-level=3") 
    options.add_argument("--silent")

    # --- PERBAIKAN BARU (MENGGANTIKAN --single-process) ---
    logging.info("Menerapkan opsi penghematan memori (mengganti --single-process)...")
    
    # 1. HAPUS --single-process: Ini mungkin penyebab crash 'Unable to receive message from renderer'
    # options.add_argument("--single-process") # DIHAPUS KARENA TIDAK STABIL
    
    # 2. Nonaktifkan gambar & fitur visual berat
    options.add_argument("--disable-images")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-software-rasterizer") # Nonaktifkan perenderan software
    options.add_argument("--disable-3d-apis") # Nonaktifkan WebGL/API 3D

    # 3. Nonaktifkan fitur-fitur latar belakang lainnya
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-breakpad") # Nonaktifkan laporan crash
    options.add_argument("--disable-component-update")
    
    # 4. Tambahkan --no-zygote, sering dipasangkan dengan --no-sandbox
    options.add_argument("--no-zygote")
    
    driver = None
    try:
        # --- PERUBAHAN UTAMA DI SINI ---
        logging.info("Tahap 2: Menyiapkan Service (mengandalkan buildpack Railway/Nixpacks)...")
        # Kita tidak lagi menggunakan ChromeDriverManager().install()
        # Kita berasumsi buildpack Railway telah menginstal chromedriver ke PATH.
        # Selenium 4+ akan menemukannya secara otomatis.
        service = Service()

        logging.info("Tahap 3: Memulai instance browser Chrome...")
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("Browser Chrome berhasil dimulai.")
        wait = WebDriverWait(driver, 120) 
        
        logging.info("Membuka halaman login CAS PENS...")
        driver.get(URL_LOGIN)
        logging.info("Memasukkan username dan password...")
        
        # Logika login
        wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(USERNAME)
        driver.find_element(By.ID, "password").send_keys(PASSWORD)
        driver.find_element(By.NAME, "submit").click()
        
        logging.info("Menunggu login berhasil...")
        wait.until(EC.url_contains("ethol.pens.ac.id/mahasiswa/beranda"))
        logging.info("Login berhasil! Kini berada di halaman Beranda.")
        time.sleep(2)

        # Navigasi ke halaman Matakuliah
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

        # Mengambil daftar mata kuliah
        logging.info("Mengambil daftar semua mata kuliah...")
        judul_matkul_elements = wait.until(EC.presence_of_all_elements_located(
            (By.XPATH, "//span[contains(@class, 'card-title-mobile')]")
        ))
        # Menggunakan set untuk memastikan daftar matkul adalah unik dan diurutkan
        nama_semua_matkul = sorted(list({judul.text.strip() for judul in judul_matkul_elements if judul.text.strip()}))
        
        if not nama_semua_matkul:
            logging.warning("Error: Tidak ada mata kuliah yang ditemukan.")
            return

        logging.info(f"Berhasil menemukan {len(nama_semua_matkul)} mata kuliah: {', '.join(nama_semua_matkul)}")

        # Loop melalui setiap mata kuliah untuk pengecekan presensi
        for nama_matkul in nama_semua_matkul:
            logging.info(f"--> Mengecek matkul: {nama_matkul}")
            try:
                # Pastikan kembali ke halaman Matakuliah jika loop sebelumnya gagal
                if "/mahasiswa/matakuliah" not in driver.current_url:
                    driver.get(URL_DAFTAR_KULIAH)
                    wait.until(EC.visibility_of_element_located(
                        (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
                    ))
                
                # Menggunakan XPATH yang lebih spesifik untuk Tombol Akses Kuliah
                tombol_akses = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//div[contains(@class, 'card-matkul') and .//span[normalize-space()='{nama_matkul}']]//button[contains(., 'Akses Kuliah')]")
                ))
                
                # Menggunakan JS Click sebagai cadangan yang lebih kuat di headless mode
                driver.execute_script("arguments[0].click();", tombol_akses)
                
                # Menunggu elemen di halaman kuliah (misalnya tombol "Aturan Presensi")
                wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[normalize-space(span)='Aturan Presensi']")
                ))
                time.sleep(1) # Beri waktu browser untuk memproses DOM

                # Mencari tombol presensi yang TIDAK dinonaktifkan
                # Gunakan XPATH yang lebih ketat: tombol 'Presensi' yang tidak memiliki atribut 'disabled'
                tombol_presensi = driver.find_element(By.XPATH, "//button[normalize-space(span)='Presensi' and not(@disabled)]")
                
                # Cek apakah tombol tersebut benar-benar terlihat dan dapat diklik (redundant check)
                if tombol_presensi.is_displayed() and tombol_presensi.is_enabled():
                    tombol_presensi.click()
                    logging.warning(f"PRESENSI DIBUKA DAN DIKLIK UNTUK: {nama_matkul}")
                    
                    # Setelah presensi ditemukan dan diklik, kita keluar dari loop
                    return # Mengganti 'break' dengan 'return' untuk mengakhiri siklus pengecekan setelah berhasil presensi
                else:
                    logging.info(f"    Tombol 'Presensi' untuk '{nama_matkul}' ditemukan tetapi dinonaktifkan/tidak terlihat.")
                    
            except NoSuchElementException:
                logging.info(f"    Presensi untuk '{nama_matkul}' masih ditutup (Tombol Presensi tidak aktif).")
            except TimeoutException:
                 logging.warning(f"    Timeout saat menunggu elemen untuk '{nama_matkul}'. Mungkin halaman tidak termuat sempurna.")
            except Exception as e:
                logging.error(f"    Terjadi error saat mengecek '{nama_matkul}': {e}", exc_info=True)
                
            # Kembali ke halaman daftar kuliah untuk mengecek mata kuliah berikutnya
            driver.get(URL_DAFTAR_KULIAH)
            wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//label[contains(text(), 'Tahun Ajaran')]")
            ))
            time.sleep(1)

    except (WebDriverException, InvalidSessionIdException) as e:
        # Menangkap error WebDriver secara umum (termasuk Status -5 dan InvalidSessionId)
        # Tambahkan log yang lebih spesifik untuk masalah Railway
        error_msg = str(e.msg if hasattr(e, 'msg') else e)
        if "Status code was: -5" in error_msg or "Status code was: -9" in error_msg or "invalid session id" in error_msg or "browser has closed" in error_msg:
            logging.critical(f"Gagal memulai Chrome. Ini SANGAT MUNGKIN masalah kehabisan memori (OOM) di Railway.")
            logging.critical("Pastikan plan Railway Anda memiliki RAM yang cukup (mis. > 512MB). Opsi penghemat memori terbaru telah diterapkan.")
        else:
            logging.critical(f"Gagal memulai atau menjalankan browser Chrome. Error: {e.msg if hasattr(e, 'msg') else e}", exc_info=True)
            
        logging.critical("Pastikan buildpack Railway (Nixpacks) menginstal google-chrome DAN chromedriver yang cocok di PATH.")
    except Exception as e:
        logging.critical(f"Terjadi error yang tidak terduga: {e}", exc_info=True)
    finally:
        if driver:
            logging.info("Menutup browser untuk siklus ini.")
            driver.quit()

if __name__ == '__main__':
    # Logika loop utama
    while True:
        logging.info(f"--- Memulai Pengecekan Siklus Baru ---")
        cek_semua_absen()
        logging.info(f"--- Siklus selesai. Siklus berikutnya dalam {INTERVAL_CEK / 60:.0f} menit. ---")
        time.sleep(INTERVAL_CEK)

