# 🚀 Mission Control Framework

Framework multi-agen modular berbasis **CrewAI** untuk mengeksekusi misi otonom secara terstruktur. Didesain *configuration-driven*: Anda cukup menyalin template misi, mengatur file `mission.yaml`, dan menjalankannya tanpa perlu memodifikasi kode framework.

---

## 📑 Daftar Isi
- [Instalasi Cepat](#-instalasi-cepat)
- [Struktur Konfigurasi (.env vs mission.yaml)](#-struktur-konfigurasi-env-vs-missionyaml)
- [Panduan Penggunaan LLM Provider](#-panduan-penggunaan-llm-provider)
  - [1. Ollama (Lokal di PC / Mac / Server)](#1-ollama-lokal)
  - [2. Groq (Cloud Gratis & Cepat)](#2-groq-cloud)
  - [3. OpenRouter (Multi-Model Cloud)](#3-openrouter-cloud)
  - [4. OpenAI Official (GPT-4o-mini / GPT-4o)](#4-openai-official)
  - [5. Anthropic Claude & Google Gemini](#5-anthropic--gemini)
  - [6. Self-Hosted Gateway (9router / OmniRoute)](#6-self-hosted-gateway-9router)
- [Cara Menjalankan Misi](#-cara-menjalankan-misi)
- [Membuat Misi Baru](#-membuat-misi-baru)
- [Daftar Tools untuk Agen](#-daftar-tools-untuk-agen)
- [Troubleshooting & Solusi Error](#-troubleshooting--solusi-error)

---

## ⚡ Instalasi Cepat

### 1. Clone Repository
```bash
git clone https://github.com/rndz1618/mission-control.git
cd mission-control
```

### 2. Setup Virtual Environment & Dependencies
```bash
# Buat virtual environment
python3 -m venv .venv

# Aktifkan virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment File (`.env`)
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Buka file `.env` dan masukkan API key provider yang akan Anda gunakan (lihat bagian konfigurasi di bawah).

---

## 🧭 Struktur Konfigurasi (`.env` vs `mission.yaml`)

Agar rapi dan aman, konfigurasi dibagi menjadi dua level:

| Lokasi | Fungsi | Contoh Konten |
|---|---|---|
| **`.env`** (Pusat Kredensial) | Menyimpan API Key, Secret Token, dan Default Base URL | `OPENAI_API_KEY`, `GROQ_API_KEY`, `OLLAMA_API_BASE`, `DISCORD_WEBHOOK_URL` |
| **`mission.yaml`** (Spesifikasi Misi) | Menentukan alur misi, daftar agen, task, tools, dan model LLM yang dipilih | `provider: groq`, `model: "llama-3.3-70b-versatile"` |

> **Aturan Keamanan:** Jangan pernah menaruh API key sensitif di dalam `mission.yaml`. Masukkan API key ke dalam `.env`.

---

## 🤖 Panduan Penggunaan LLM Provider

Pilih provider yang Anda inginkan dengan mengatur `.env` dan `mission.yaml`:

### 1. Ollama (Lokal)
Cocok jika Anda menjalankan Ollama di komputer lokal atau server internal:
- **Di `.env`**:
  ```bash
  OLLAMA_API_BASE=http://localhost:11434   # Ganti IP jika Ollama ada di PC lain
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: ollama
    model: "llama3.2"                     # atau qwen2.5, mistral, deepseek-r1
    temperature: 0.7
  ```

### 2. Groq (Cloud)
Sangat direkomendasikan jika ingin inferensi gratis, stabil, dan sangat cepat:
- **Di `.env`**:
  ```bash
  GROQ_API_KEY=gsk_your_groq_api_key_here
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: groq
    model: "llama-3.3-70b-versatile"
    temperature: 0.7
  ```

### 3. OpenRouter (Cloud)
Akses ratusan model open-source dan proprietary dalam satu kunci:
- **Di `.env`**:
  ```bash
  OPENROUTER_API_KEY=sk-or-v1-your_key_here
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: openrouter
    model: "meta-llama/llama-3.3-70b-instruct"  # atau anthropic/claude-3.5-haiku
    temperature: 0.7
  ```

### 4. OpenAI Official
- **Di `.env`**:
  ```bash
  OPENAI_API_KEY=sk-proj-your_openai_api_key_here
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: openai
    model: "gpt-4o-mini"
    temperature: 0.7
  ```

### 5. Anthropic / Gemini
- **Di `.env`**:
  ```bash
  ANTHROPIC_API_KEY=sk-ant-...
  GEMINI_API_KEY=AIzaSy...
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: anthropic   # atau gemini
    model: "claude-3-5-haiku-20241022" # atau gemini-1.5-flash
  ```

### 6. Self-Hosted Gateway (9router / OmniRoute / Local vLLM)
Jika menjalankan gateway lokal:
- **Di `.env`**:
  ```bash
  OPENAI_API_BASE=http://localhost:20128/v1
  OPENAI_API_KEY=sk-your_gateway_key
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: openai
    model: "gh/gpt-4o-mini-2024-07-18"
  ```

---

## 🏃 Cara Menjalankan Misi

Jalankan perintah berikut:
```bash
python run_mission.py <nama_misi>
```

**Contoh:**
```bash
# Menjalankan misi bawaan arah_media
python run_mission.py arah_media
```

---

## 🛠️ Membuat Misi Baru

1. Salin template misi:
   ```bash
   cp -r missions/template missions/nama_misi_anda
   mv missions/nama_misi_anda/mission_template.yaml missions/nama_misi_anda/mission.yaml
   ```
2. Buka `missions/nama_misi_anda/mission.yaml` dan sesuaikan:
   - `mission.overall_goal`: Tujuan besar misi.
   - `agents`: Daftar peran agen, keahlian (`backstory`), dan tools yang diizinkan.
   - `tasks`: Alur kerja bertahap, konteks ketergantungan antar task (`context:`).
   - `llm`: Provider & model yang digunakan.
3. Eksekusi:
   ```bash
   python run_mission.py nama_misi_anda
   ```

---

## 🧰 Daftar Tools untuk Agen

Setiap agen dapat diberikan tool spesifik di bawah field `tools:` pada `mission.yaml`:

| Tool Key | Kategori | Deskripsi |
|---|---|---|
| `x_search` | Social | Mencari postingan di X / Twitter |
| `x_post_tweet` | Social | Memposting tweet tunggal |
| `x_post_thread` | Social | Memposting rangkaian thread tweet |
| `x_get_tweet` | Social | Mengambil detail tweet berdasarkan ID |
| `notion_search` | Workspace | Mencari dokumen / halaman di Notion |
| `notion_read_page` | Workspace | Membaca isi halaman Notion |
| `notion_create_page` | Workspace | Membuat halaman dokumen baru |
| `notion_update_page` | Workspace | Memperbarui isi dokumen Notion |
| `market_data_ticker` | Market | Cek harga real-time kripto / aset |
| `market_data_ohlcv` | Market | Data candlestick teknikal |
| `market_data_trend` | Market | Analisis indikator teknikal (SMA, RSI, MACD) |
| `discord_tool` | Notifikasi | Mengirim pesan / laporan ke Discord via Webhook |

---

## 🔍 Troubleshooting & Solusi Error

#### 1. `Failed to connect to OpenAI API: Connection error`
- **Penyebab:** Endpoint yang dituju (`base_url`) mati atau tidak dapat diakses dari mesin Anda (misal `http://localhost:20128` saat berjalan di Codespaces atau PC luar).
- **Solusi:**
  - Jika ingin pakai Cloud (Groq, OpenRouter, OpenAI), isi API key di `.env` dan set provider di `mission.yaml`.
  - Jika pakai Ollama, pastikan service Ollama sudah aktif (`ollama serve`).

#### 2. `python-dotenv could not parse statement starting at line X`
- **Penyebab:** Format penulisan pada file `.env` mengandung karakter ilegal atau kutip yang tidak tertutup.
- **Solusi:** Pastikan `.env` menggunakan format `KEY=VALUE` standar tanpa tanda kutip ganda yang tertinggal.

#### 3. `API key not found for provider 'xxx'`
- **Penyebab:** Environment variable belum di-set di file `.env`.
- **Solusi:** Buka `.env` dan tambahkan key yang sesuai (contoh: `GROQ_API_KEY=gsk_...`).

---

## 🧪 Menjalankan Test Framework
Untuk memverifikasi integritas arsitektur:
```bash
python test_framework.py
```
