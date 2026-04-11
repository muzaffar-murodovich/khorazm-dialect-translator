# Khorezm Dialect Translator

A web-based translator that converts Khorezm regional dialect (sheva) words into standard literary Uzbek. Built as a diploma project ("Diplom loyiha").

## Architecture

Flask web app with a dictionary-based translation engine. No database — the dictionary is loaded from a CSV file at startup.

```
app.py              – Flask app: serves UI and /api/translate endpoint
translator.py       – Core translation logic + dictionary loading
wsgi.py             – Gunicorn WSGI entry point
requirements.txt    – Production dependencies
templates/
  index.html        – Single-page Jinja2 template
static/
  script.js         – Frontend: debounced fetch to /api/translate, copy/clear buttons
  style.css         – Responsive CSS (mobile breakpoint at 640px)
data/
  output.csv        – Birlashtirilgan lugʻat (~3486 yozuv, Title/Meaning ustunlari)
deploy/
  deploy.sh                     – Server setup script (Gunicorn + Nginx)
  server-info.md                – Server credentials (gitignored)
  gunicorn-translator.service   – systemd service file (gitignored)
  translator.nginx              – Nginx site config (gitignored)
.github/
  workflows/
    deploy.yml      – CI/CD: auto-deploy on push to master
```

## Dictionary

`data/output.csv` — birlashtirilgan lugʻat (scraper + Excel manbalardan). `Title` va `Meaning` ustunlari. Kirill va Lotin aralash — `translator.py` yuklaganda hammasini Lotinga oʻgiradi.

## Translation Engine (translator.py)

Key concepts:
- **Cyrillic→Latin transliteration**: Applied to dictionary entries at load time via `translit_map`
- **Two dictionaries**: `single_dict` (single words) and `phrase_dict` (multi-word phrases)
- **`_extract_short_meaning`**: Filters out long definitions — keeps entries ≤6 words or short first clause ≤3 words
- **Translation order**: (1) multi-word phrases (up to 3 words) → (2) exact single word → (3) suffix-stripped stem lookup → (4) leave unchanged
- **Suffix stripping**: Uzbek suffixes (`SUFFIXES` list) are removed to find root forms; the suffix is re-appended to the translation
- **Case preservation**: `_match_case` copies original casing to the replacement
- **Tokenization**: regex-based, preserves whitespace and punctuation between tokens

## Development

### Setup & Run
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000
```

### Dependencies (requirements.txt)
- **flask** — web framework
- **gunicorn** — WSGI server (production)
- **beautifulsoup4** — HTML parsing

### No tests or linting configured
There are no test files, test framework, or linter/formatter configs in this project.

## Deployment

- **Server**: Hetzner CX23, Ubuntu 24.04 — domain `xorazmcha.muzaffar.zip`
- **Stack**: Cloudflare → Nginx (port 80) → Gunicorn (unix socket) → Flask
- **CI/CD**: GitHub Actions — push to `master` triggers auto-deploy via SSH
- **Setup**: Run `deploy/deploy.sh` on server for initial setup (Gunicorn service + Nginx config)

## Key Conventions

- **Language**: Code comments and UI text are in Uzbek (Latin script)
- **API**: Single POST endpoint `/api/translate` — accepts `{"text": "..."}`, returns `{"translated", "translated_count", "total_words"}`
- **Frontend**: Vanilla JS, no build step. Debounced translation (350ms) on input
- **Git**: Hosted on GitHub, auto-deploys on push to `master`
