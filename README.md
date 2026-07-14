# ISPU Jakarta Scraper

Script Python untuk mengambil (scraping) data historis kualitas udara **ISPU (Indeks Standar Pencemar Udara)** dari situs resmi [rendahemisi.jakarta.go.id](https://rendahemisi.jakarta.go.id/ispu), lalu menyimpannya ke dalam file CSV untuk keperluan analisis data.

## ✨ Fitur

- Mengambil data ISPU harian dari **5 stasiun pemantauan DKI Jakarta**:
  - DKI1 Bundaran HI
  - DKI2 Kelapa Gading
  - DKI3 Jagakarsa
  - DKI4 Lubang Buaya
  - DKI5 Kebun Jeruk
- Mendukung rentang tanggal kustom (`START_DATE` s/d `END_DATE`)
- Sistem **fallback jam**: mencoba beberapa jam target (23:00, 00:00, 20:00, dst.) jika data pada jam utama tidak tersedia
- **Resume otomatis** — jika proses terhenti, script akan melanjutkan dari data yang belum diambil tanpa mengulang dari awal
- Penyimpanan berkala (auto-save setiap 50 record baru) agar data tidak hilang jika terjadi error
- Logging aktivitas dan error ke file `scraping_log.txt`
- Jeda antar request acak (1–2 detik) untuk menghindari pemblokiran oleh server

## 📦 Data yang Diambil

Untuk setiap kombinasi stasiun dan tanggal, script menyimpan kolom berikut:

| Kolom | Keterangan |
|---|---|
| `tanggal` | Tanggal pengukuran (YYYY-MM-DD) |
| `jam_diambil` | Jam data yang berhasil diambil |
| `stasiun_id` | ID stasiun pemantauan |
| `stasiun` | Nama stasiun |
| `pm10` | Konsentrasi PM10 |
| `pm25` | Konsentrasi PM2.5 |
| `so2` | Konsentrasi SO2 |
| `co` | Konsentrasi CO |
| `o3` | Konsentrasi O3 |
| `no2` | Konsentrasi NO2 |
| `kategori` | Kategori kualitas udara (Baik, Sedang, Tidak Sehat, dll.) |
| `url` | URL sumber data |

## 🛠️ Instalasi

Pastikan Python 3.10+ sudah terpasang, lalu install dependency yang dibutuhkan:

```bash
pip install requests beautifulsoup4 pandas
```

## 🚀 Cara Menggunakan

1. Sesuaikan konfigurasi di bagian atas file `ispu_scraper.py` sesuai kebutuhan:

```python
START_DATE   = datetime(2025, 12, 1)
END_DATE     = datetime(2025, 12, 31)
OUTPUT_FILE  = "ispu_jakarta_harian_desember.csv"
```

2. Jalankan script:

```bash
python ispu_scraper.py
```

3. Data akan tersimpan otomatis ke file CSV yang ditentukan di `OUTPUT_FILE`, dan log proses akan tercatat di `scraping_log.txt`.

Jika proses terhenti di tengah jalan (misalnya karena koneksi terputus), cukup jalankan ulang perintah yang sama — script akan otomatis melanjutkan dari data yang belum diambil berkat mekanisme resume.

## ⚠️ Catatan & Etika Scraping

- Script ini menyertakan jeda (delay) antar request secara acak untuk mengurangi beban pada server sumber data.
- Gunakan secara bertanggung jawab dan sesuai dengan [ketentuan penggunaan](https://rendahemisi.jakarta.go.id/) situs sumber.
- Data yang diambil bersifat publik dan disediakan oleh Dinas Lingkungan Hidup DKI Jakarta, hanya digunakan untuk kepentingan riset/analisis non-komersial.
- Struktur halaman web sumber dapat berubah sewaktu-waktu, yang berpotensi memerlukan penyesuaian pada logika parsing.

## 📄 Lisensi

Silakan gunakan dan modifikasi script ini secara bebas untuk keperluan riset atau analisis data kualitas udara.
