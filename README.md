# 🚀 Mission Control Framework

Framework modular berbasis CrewAI untuk menjalankan berbagai jenis "misi" otonom secara terstruktur. Didesain agar mudah diduplikasi: cukup salin folder misi, edit file `mission.yaml`, dan jalankan!

---

## 📁 Struktur Direktori

```
/root/mission-control/
├── .venv/                      # Python Virtual Environment
├── .env                        # Konfigurasi Environment & API Keys
├── requirements.txt            # Dependencies
├── run_mission.py              # Script utama untuk menjalankan misi
├── test_framework.py           # Unit & Integration Tests
│
├── framework/                  # Core Framework (JANGAN DIUBAH)
│   ├── __init__.py
│   ├── crew_builder.py         # Parser YAML & Builder CrewAI
│   ├── tools/                  # Wrapper Tool untuk Agen
│   │   ├── __init__.py
│   │   ├── notion_tool.py      # Integrasi Notion via `ntn` CLI
│   │   ├── x_tool.py           # Integrasi Twitter/X via `xurl` CLI
│   │   ├── market_data_tool.py # Integrasi Market Data Ingestion
│   │   └── discord_tool.py     # Integrasi Notifikasi Discord Webhook
│   └── configs/
│       ├── base_agent_template.yaml
│       └── base_task_template.yaml
│
└── missions/                   # Kumpulan Misi Anda
    ├── arah_media/             # Misi Pertama: Strategi Konten Media
    │   └── mission.yaml
    └── template/               # Template untuk Membuat Misi Baru
        └── mission_template.yaml
```

---

## ⚡ Cara Menjalankan Misi

### 1. Menjalankan Misi yang Sudah Ada
```bash
cd /root/mission-control
.venv/bin/python run_mission.py arah_media
```

### 2. Membuat & Menjalankan Misi Baru
1. Buat folder baru di bawah `missions/`:
   ```bash
   cp -r missions/template missions/nama_misi_baru
   mv missions/nama_misi_baru/mission_template.yaml missions/nama_misi_baru/mission.yaml
   ```
2. Edit file `missions/nama_misi_baru/mission.yaml` sesuai kebutuhan (tujuan, role agen, task, tools).
3. Jalankan:
   ```bash
   .venv/bin/python run_mission.py nama_misi_baru
   ```

---

## 🛠️ Tool yang Tersedia untuk Agen

Setiap agen dapat diberikan tool spesifik di bawah field `tools:` pada `mission.yaml`:

| Tool Name | Fungsi | Parameter Contoh |
|---|---|---|
| `x_search` | Cari tweet di X/Twitter | `{"query": "AI trends", "count": 5}` |
| `x_post_tweet` | Posting tweet ke X | `{"text": "Halo dunia!"}` |
| `x_post_thread` | Posting thread ke X | `{"tweets": ["Tweet 1", "Tweet 2"]}` |
| `x_get_tweet` | Baca detail tweet | `{"tweet_id": "123456"}` |
| `notion_search` | Cari halaman di Notion | `{"query": "proyek"}` |
| `notion_read_page` | Baca isi halaman Notion | `{"page_id": "abc123"}` |
| `notion_create_page` | Buat halaman baru di Notion | `{"parent_id": "abc", "title": "Judul"}` |
| `notion_update_page` | Update halaman Notion | `{"page_id": "abc", "content": "Update"}` |
| `market_data_ticker` | Cek harga real-time kripto | `{"symbol": "BTC/USDT"}` |
| `market_data_ohlcv` | Ambil data candlestick | `{"symbol": "BTC/USDT", "timeframe": "1h"}` |
| `market_data_trend` | Analisis teknikal & indikator | `{"symbol": "BTC/USDT", "lookback": 50}` |
| `discord_tool` | Kirim notifikasi webhook Discord | `{"message": "Halo dari Agent!"}` |

---

## 🧪 Menjalankan Tests

Untuk memastikan seluruh arsitektur framework berjalan normal:
```bash
cd /root/mission-control
.venv/bin/python test_framework.py
```

---

## ⚙️ Konfigurasi LLM

Secara default, misi menggunakan gateway lokal **9router** yang berjalan di server:
- **Base URL:** `http://localhost:20128/v1`
- **Default Model:** `gh/gpt-4o-mini-2024-07-18`
- Anda bisa mengubah model per misi di bagian bawah `mission.yaml`:
  ```yaml
  llm:
    model: "gh/gpt-4o-mini-2024-07-18"
    base_url: "http://localhost:20128/v1"
    temperature: 0.7
  ```
