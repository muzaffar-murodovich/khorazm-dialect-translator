# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
  output_clean.csv  – Birlashtirilgan lugʻat (~3486 yozuv, Title/Meaning ustunlari)
  merge_dicts.py    – Lugʻatlarni birlashtirish skripti
  csv_clean.py      – CSV tozalash/standartlashtirish skripti
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

`data/output_clean.csv` — birlashtirilgan lugʻat (scraper + Excel manbalardan). `Title` va `Meaning` ustunlari. Kirill va Lotin aralash — `translator.py` yuklaganda hammasini Lotinga oʻgiradi.

Lugʻat ikkita Python `dict` ga boʻlinadi:
- `single_dict` — bir soʻzli kalitlar (406 ta)
- `phrase_dict` — koʻp soʻzli iboralar (2+ soʻz)

`load_fromexcel()` qoʻshimcha lugʻat (`fromexcel.csv`, `dialect`/`literary` ustunlari) yuklaydi — mavjud kalitlar ustidan yozmaydi.

## Translation Engine (translator.py)

### Tarjima bosqichlari (priority order):
1. **Koʻp soʻzli iboralar** (phrase_dict, 3 va 2 soʻz)
2. **Aniq soʻz mosligi** (single_dict)
3. **Fe'l morfologik tahlil** — sheva fe'l ildizlari va suffikslarini adabiy shaklga oʻgiradi
4. **Nom suffiksi qirqish** — kelishik/koʻplik suffikslarini ajratib, ildizni lugʻatdan qidiradi
5. **Oʻzgartirilmay qoladi** — lugʻatda topilmagan soʻzlar

### Apostrof normallashtirish
`_normalize_apostrophe()` — `'` (U+0027), `ʼ` (U+02BC) → `ʻ` (U+02BB) ga oʻgiradi. Lugʻat kalitlari va foydalanuvchi kiritgan matn bir xil tutuq belgisi bilan solishtirilishi uchun barcha qidiruv yoʻllarida qoʻllanadi (`load_dictionary`, `load_fromexcel`, `translate`, `_strip_suffix`).

`_normalize()` esa apostroflarni butunlay **oʻchiradi** — faqat fe'l ishlovi uchun (VERB_ROOT_MAP va VERB_SUFFIX_MAP kalitlarida apostrof yoʻq). Shuningdek sheva yozuvidagi variant belgilarni standartlashtiradi: `ø/ö → ө`, `ü/ú → ү`.

### Fe'l morfologiyasi
- `VERB_SUFFIX_MAP` — sheva fe'l suffikslarini adabiy shaklga moslaydi (83 ta)
- `VERB_ROOT_MAP` — sheva fe'l ildizlarini adabiy shaklga moslaydi (78 ta)
- `strip_verb_suffix()` — soʻzdan sheva fe'l suffiksini ajratadi (uzunlik boʻyicha tartiblangan)
- `translate_verb()` — toʻliq fe'l morfologik tahlil: suffiks ajratish → ildiz almashtirish → suffiks almashtirish → birlashtirish

### Boshqa yordamchi funksiyalar
- `transliterate()` — Kirill → Lotin (Cyrillic→Latin) oʻgirish, lugʻat yuklashda ishlatiladi
- `_extract_short_meaning()` — uzun izohlardan qisqa tarjima alternativini ajratadi (≤6 soʻz yoki birinchi qisqa qism)
- `_match_case()` — asl soʻz registrini (katta/kichik harf) tarjimaga koʻchiradi
- `_strip_suffix()` — ot/ravish suffikslarini qirqadi (kelishik, koʻplik, egalik)
- `tokenize()` — regex asosida matnni soʻz va tinish belgilariga ajratadi, apostrof variantlarini soʻz tarkibida qoldiradi
- `SUFFIXES` — 30 ta umumiy nom suffikslari (uzunlik boʻyicha)

## Development

### Setup & Run
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# → http://127.0.0.1:5000
```

### Quick test via Python
```bash
python3 -c "
from translator import translate, single_dict, phrase_dict
print(translate('boʻkchi', single_dict, phrase_dict))
"
```

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
