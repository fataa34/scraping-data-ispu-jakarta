import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import random

# ============================================================
# KONFIGURASI
# ============================================================

STATIONS = [
    {"id": 4, "slug": "dki1-bundaran-hi",   "nama": "DKI1 Bundaran HI"},
    {"id": 5, "slug": "dki2-kelapa-gading", "nama": "DKI2 Kelapa Gading"},
    {"id": 6, "slug": "dki3-jagakarsa",     "nama": "DKI3 Jagakarsa"},
    {"id": 7, "slug": "dki4-lubang-buaya",  "nama": "DKI4 Lubang Buaya"},
    {"id": 8, "slug": "dki5-kebun-jeruk",   "nama": "DKI5 Kebun Jeruk"},
]

# Jam yang ingin diambil — prioritas 23:00, fallback ke 00:00
TARGET_HOURS = ["23:00", "00:00", "20:00", "15:00", "10:00"]  # Tambahan fallback jika 3 jam utama tidak ada

START_DATE   = datetime(2025, 12, 1)
END_DATE     = datetime(2025, 12, 31)   # Kemarin (data hari ini belum lengkap)
OUTPUT_FILE  = "ispu_jakarta_harian_desember.csv"
LOG_FILE     = "scraping_log.txt"

BASE_URL = "https://rendahemisi.jakarta.go.id/ispu-detail"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://rendahemisi.jakarta.go.id/ispu",
}


# ============================================================
# FUNGSI SCRAPING SATU HALAMAN
# ============================================================

def scrape_one_day(station: dict, date: datetime) -> dict | None:
    """
    Ambil data satu hari untuk satu stasiun.
    Prioritas jam: 23:00 → 00:00 → 22:00
    Kembalikan dict satu baris, atau None jika tidak ada data.
    """
    date_str = date.strftime("%d-%m-%Y")  # Format: DD-MM-YYYY
    url = f"{BASE_URL}/{station['id']}/{station['slug']}/{date_str}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        log(f"ERROR {station['nama']} {date_str}: {e}")
        return None

    soup = BeautifulSoup(r.text, "html.parser")

    # Cari tabel dengan kolom "Waktu"
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if not header_row:
            continue
        col_names = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]
        if "Waktu" not in col_names:
            continue

        # Baca semua baris ke dict
        rows = {}
        for row in table.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= len(col_names):
                d = dict(zip(col_names, cells))
                waktu = d.get("Waktu", "")
                rows[waktu] = d

        # Pilih jam terbaik yang tersedia
        chosen = None
        chosen_hour = None
        for hour in TARGET_HOURS:
            if hour in rows and rows[hour].get("PM 2.5", "-") != "-":
                chosen = rows[hour]
                chosen_hour = hour
                break

        if not chosen:
            log(f"NODATA {station['nama']} {date_str}: semua jam kosong")
            return None

        return {
            "tanggal":      date.strftime("%Y-%m-%d"),
            "jam_diambil":  chosen_hour,
            "stasiun_id":   station["id"],
            "stasiun":      station["nama"],
            "pm10":         to_float(chosen.get("PM 10")),
            "pm25":         to_float(chosen.get("PM 2.5")),
            "so2":          to_float(chosen.get("SO2")),
            "co":           to_float(chosen.get("CO")),
            "o3":           to_float(chosen.get("O3")),
            "no2":          to_float(chosen.get("NO2")),
            "kategori":     chosen.get("Kategori", "-"),
            "url":          url,
        }

    log(f"NOTABLE {station['nama']} {date_str}: tabel tidak ditemukan")
    return None


def to_float(val: str) -> float | None:
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ============================================================
# LOGGING
# ============================================================

def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(f"  {line}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ============================================================
# RESUME: Cek tanggal+stasiun yang sudah diproses
# ============================================================

def load_done_keys() -> set:
    """Baca CSV yang sudah ada, return set (tanggal, stasiun_id) yang sudah ada."""
    if not os.path.isfile(OUTPUT_FILE):
        return set()
    try:
        df = pd.read_csv(OUTPUT_FILE, usecols=["tanggal", "stasiun_id"])
        return set(zip(df["tanggal"], df["stasiun_id"].astype(str)))
    except Exception:
        return set()


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    print("=" * 60)
    print("  ISPU Jakarta Scraper — rendahemisi.jakarta.go.id")
    print(f"  Rentang : {START_DATE.date()} s/d {END_DATE.date()}")
    print(f"  Stasiun : {len(STATIONS)} stasiun DKI")
    print(f"  Target  : Jam {TARGET_HOURS}")
    print("=" * 60)

    # Hitung total request
    total_days = (END_DATE - START_DATE).days + 1
    total_req  = total_days * len(STATIONS)
    print(f"\nEstimasi request: {total_days} hari × {len(STATIONS)} stasiun = {total_req:,} request")
    print(f"Estimasi waktu  : ~{total_req * 1.5 / 3600:.1f} jam (dengan jeda 1.5 detik/request)\n")

    # Load progress sebelumnya (resume jika terhenti)
    done_keys = load_done_keys()
    print(f"Progress sebelumnya: {len(done_keys)} kombinasi sudah selesai\n")

    all_new_records = []
    file_exists = os.path.isfile(OUTPUT_FILE)
    request_count = 0

    current_date = START_DATE
    while current_date <= END_DATE:
        date_str_display = current_date.strftime("%Y-%m-%d")

        for station in STATIONS:
            key = (date_str_display, str(station["id"]))

            # Skip jika sudah pernah diproses
            if key in done_keys:
                continue

            record = scrape_one_day(station, current_date)
            request_count += 1

            if record:
                all_new_records.append(record)
                print(f"  ✓ {date_str_display} | {station['nama']:25s} | "
                      f"PM2.5={record['pm25']:6} | {record['kategori']}")

            # Simpan setiap 50 record baru
            if len(all_new_records) >= 50:
                save_records(all_new_records, file_exists)
                file_exists = True
                all_new_records = []

            # Jeda antar request (1–2 detik, acak agar tidak terblokir)
            time.sleep(random.uniform(1.0, 2.0))

        current_date += timedelta(days=1)

    # Simpan sisa record
    if all_new_records:
        save_records(all_new_records, file_exists)

    print(f"\n✓ Selesai! Total request: {request_count:,}")
    print(f"  Data disimpan di: {OUTPUT_FILE}")

    # Tampilkan ringkasan
    if os.path.isfile(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE)
        print(f"\nRingkasan dataset:")
        print(f"  Total baris : {len(df):,}")
        print(f"  Rentang     : {df['tanggal'].min()} s/d {df['tanggal'].max()}")
        print(f"  Stasiun     : {df['stasiun'].nunique()} stasiun")
        print(f"\nPreview:\n{df.tail(10).to_string(index=False)}")


def save_records(records: list, file_exists: bool):
    df = pd.DataFrame(records)
    df.to_csv(OUTPUT_FILE, mode="a", header=not file_exists, index=False, encoding="utf-8-sig")
    print(f"\n  [SAVED] {len(records)} record baru → {OUTPUT_FILE}\n")


# ============================================================
if __name__ == "__main__":
    main()