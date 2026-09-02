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
  - [Eksekusi Standar](#1-eksekusi-standar)
  - [Eksekusi dengan Variabel Input Dinamis (`--input`)](#2-eksekusi-dengan-variabel-input-dinamis---input)
  - [Human-in-the-Loop (`human_input: true`)](#3-human-in-the-loop-approval-interaktif)
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
Buka file `.env` dan masukkan API key provider yang akan Anda gunakan.

---

## 🧭 Struktur Konfigurasi (`.env` vs `mission.yaml`)

Agar rapi dan aman, konfigurasi dibagi menjadi dua level:

| Lokasi | Fungsi | Contoh Konten |
|---|---|---|
| **`.env`** (Pusat Kredensial) | Menyimpan API Key, Secret Token, dan Default Base URL | `OPENAI_API_KEY`, `GROQ_API_KEY`, `OLLAMA_API_BASE`, `DISCORD_WEBHOOK_URL` |
| **`mission.yaml`** (Spesifikasi Misi) | Menentukan alur misi, daftar agen, task, tools, dan model LLM yang dipilih | `provider: groq`, `model: "llama-3.3-70b-versatile"` |

---

## 🤖 Panduan Penggunaan LLM Provider

Pilih provider yang Anda inginkan dengan mengatur `.env` dan `mission.yaml`:

### 1. Ollama (Lokal)
- **Di `.env`**:
  ```bash
  OLLAMA_API_BASE=http://localhost:11434
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: ollama
    model: "llama3.2"
    temperature: 0.7
  ```

### 2. Groq (Cloud Gratis & Cepat)
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
- **Di `.env`**:
  ```bash
  OPENROUTER_API_KEY=sk-or-v1-your_key_here
  ```
- **Di `mission.yaml`**:
  ```yaml
  llm:
    provider: openrouter
    model: "meta-llama/llama-3.3-70b-instruct"
    temperature: 0.7
  ```

---

## 🏃 Cara Menjalankan Misi

### 1. Eksekusi Standar
```bash
python run_mission.py arah_media
```

### 2. Eksekusi dengan Variabel Input Dinamis (`--input`)
Anda dapat menyisipkan variabel placeholder di dalam deskripsi task di `mission.yaml` (misal `{topic}`, `{audience}`), lalu mengirim nilainya langsung saat menjalankan command:

```bash
python run_mission.py arah_media -i topic="Tren AI Coding Agents 2026" -i audience="Software Engineer"
```
Atau menggunakan raw JSON:
```bash
python run_mission.py arah_media --inputs-json '{"topic": "AI Coding Agents", "audience": "Software Engineer"}'
```

### 3. Human-in-the-Loop (Approval Interaktif)
Jika Anda ingin suatu task berhenti dan meminta review / revisi dari Anda sebelum dilanjutkan ke task berikutnya, tambahkan `human_input: true` pada task terkait di `mission.yaml`:

```yaml
tasks:
  - agent: Content Editor
    description: >
      Review draft konten dan minta persetujuan human sebelum diteruskan ke rilis.
    expected_output: >
      Draft final yang telah disetujui.
    human_input: true    # 👈 Terminal akan pause dan meminta respon teks Anda!
```

---

## 🛠️ Membuat Misi Baru

1. Salin template misi:
   ```bash
   cp -r missions/template missions/nama_misi_baru
   mv missions/nama_misi_baru/mission_template.yaml missions/nama_misi_baru/mission.yaml
   ```
2. Buka `missions/nama_misi_baru/mission.yaml` dan sesuaikan:
   - `mission.overall_goal`: Tujuan besar misi.
   - `agents`: Daftar peran agen, keahlian (`backstory`), dan tools yang diizinkan.
   - `tasks`: Alur kerja bertahap, konteks ketergantungan antar task (`context:`).
   - `llm`: Provider & model yang digunakan.
3. Eksekusi:
   ```bash
   python run_mission.py nama_misi_baru
   ```

---

## 🧰 Daftar Tools untuk Agen

Setiap agen dapat diberikan tool spesifik di bawah field `tools:` pada `mission.yaml`:

| Tool Key | Kategori | Deskripsi | Fallback Behavior |
|---|---|---|---|
| `x_search` | Social | Mencari postingan di X / Twitter | Graceful notice jika `xurl` tidak ada di sistem |
| `x_post_tweet` | Social | Memposting tweet tunggal | Simulasi output jika `xurl` tidak ada di sistem |
| `x_post_thread` | Social | Memposting thread tweet | Simulasi output jika `xurl` tidak ada di sistem |
| `x_get_tweet` | Social | Mengambil tweet by ID | Graceful notice jika `xurl` tidak ada |
| `notion_search` | Workspace | Mencari dokumen di Notion | Membutuhkan `ntn` CLI |
| `notion_read_page` | Workspace | Membaca isi halaman Notion | Membutuhkan `ntn` CLI |
| `notion_create_page` | Workspace | Membuat halaman dokumen baru | Membutuhkan `ntn` CLI |
| `notion_update_page` | Workspace | Memperbarui isi dokumen Notion | Membutuhkan `ntn` CLI |
| `market_data_ticker` | Market | Cek harga real-time kripto / aset | Membutuhkan ingest script |
| `market_data_ohlcv` | Market | Data candlestick teknikal | Membutuhkan ingest script |
| `market_data_trend` | Market | Analisis indikator (SMA, RSI) | Membutuhkan ingest script |
| `discord_tool` | Notifikasi | Mengirim pesan webhook ke Discord | Membutuhkan `DISCORD_WEBHOOK_URL` di `.env` |

---

## 🔍 Troubleshooting & Solusi Error

#### 1. `Failed to connect to OpenAI API: Connection error`
- **Penyebab:** Endpoint yang dituju (`base_url`) mati atau tidak dapat diakses dari mesin Anda.
- **Solusi:**
  - Jika pakai Cloud (Groq, OpenRouter, OpenAI), isi API key di `.env` dan set provider di `mission.yaml`.
  - Jika pakai Ollama, pastikan service Ollama sudah aktif (`ollama serve`).

#### 2. `Notice: 'xurl' CLI is not installed`
- **Penyebab:** CLI binary `xurl` belum terpasang di environment sistem Anda.
- **Solusi:** Tool `x_tool` akan otomatis menangani ini dengan aman (graceful notice). Jika tidak membutuhkan live search Twitter, Anda juga bisa mengosongkan `tools: []` pada agen tersebut.

#### 3. `API key not found for provider 'xxx'`
- **Penyebab:** Environment variable belum di-set di file `.env`.
- **Solusi:** Buka `.env` dan tambahkan key yang sesuai (contoh: `GROQ_API_KEY=gsk_...`).

---

## 🧪 Menjalankan Test Framework
Untuk memverifikasi integritas arsitektur:
```bash
python test_framework.py
```
