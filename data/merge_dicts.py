"""
merge_dicts.py
==============
fromexcel.csv va output.csv ni birlashtiradi.

Ishlatish:
    python merge_dicts.py

Natija:
    output.csv — kengaytirilgan, birlashtilgan lug'at

Qoidalar:
    - output.csv yozuvlari USTUVOR (qayta yozilmaydi)
    - fromexcel.csv dan faqat yangi, lug'atda yo'q so'zlar qo'shiladi
    - Bo'sh yoki "Mavjud emas" literary qatorlar o'tkazib yuboriladi
    - Ko'p ma'noli literary matndan birinchi qisqa ma'no olinadi
    - Natijada ustunlar: Title (Lotin), Meaning (Lotin)
"""

import csv
import re
import os

# ---------------------------------------------------------------------------
# Yo'llar
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV  = os.path.join(BASE_DIR, "output.csv")
EXCEL_CSV   = os.path.join(BASE_DIR, "data & manipulating", "fromexcel.csv")
BACKUP_CSV  = os.path.join(BASE_DIR, "output_backup.csv")

# ---------------------------------------------------------------------------
# Kirill → Lotin transliteratsiya
# ---------------------------------------------------------------------------
_TRANSLIT = {
    "А":"A","а":"a","Б":"B","б":"b","В":"V","в":"v","Г":"G","г":"g",
    "Д":"D","д":"d","Е":"E","е":"e","Ё":"Yo","ё":"yo","Ж":"J","ж":"j",
    "З":"Z","з":"z","И":"I","и":"i","Й":"Y","й":"y","К":"K","к":"k",
    "Л":"L","л":"l","М":"M","м":"m","Н":"N","н":"n","О":"O","о":"o",
    "П":"P","п":"p","Р":"R","р":"r","С":"S","с":"s","Т":"T","т":"t",
    "У":"U","у":"u","Ф":"F","ф":"f","Х":"X","х":"x","Ц":"Ts","ц":"ts",
    "Ч":"Ch","ч":"ch","Ш":"Sh","ш":"sh","Щ":"Sh","щ":"sh",
    "Ъ":"","ъ":"","Ь":"","ь":"","Э":"E","э":"e","Ю":"Yu","ю":"yu",
    "Я":"Ya","я":"ya","Ў":"Oʻ","ў":"oʻ","Қ":"Q","қ":"q",
    "Ғ":"Gʻ","ғ":"gʻ","Ҳ":"H","ҳ":"h",
}

def transliterate(text: str) -> str:
    return "".join(_TRANSLIT.get(ch, ch) for ch in text)


# ---------------------------------------------------------------------------
# Yordamchi funksiyalar
# ---------------------------------------------------------------------------

def clean_key(word: str) -> str:
    """Kalit so'zni normalizatsiya qiladi."""
    key = word.strip().lower()
    key = re.sub(r"\(.*?\)", "", key).strip()   # qavslarni olib tashlash
    key = re.sub(r"\s+", " ", key)              # ortiqcha bo'shliqlar
    return key


def extract_short_meaning(meaning: str) -> str | None:
    """
    Uzun izohlangan matndan qisqa tarjima variantini ajratadi.
    - Raqamli ro'yhat boshlanishini olib tashlaydi: "1. so'z"  → "so'z"
    - Bo'sh yoki 'mavjud emas' bo'lsa None qaytaradi
    - 6 so'zdan qisqa bo'lsa to'liq qaytaradi
    - Uzun bo'lsa vergul/nuqtagacha bo'lgan <=3 so'zli birinchi qismni qaytaradi
    """
    m = meaning.strip()
    if not m or m.lower() in ("nan", "mavjud emas", "not attested", ""):
        return None

    # "1. so'z" → "so'z"
    m = re.sub(r"^\d+[\.\)]\s*", "", m).strip()
    if not m:
        return None

    words = m.split()
    if len(words) <= 6:
        return m

    for sep in [";", ",", "."]:
        idx = m.find(sep)
        if idx != -1:
            first = m[:idx].strip()
            if 1 <= len(first.split()) <= 3:
                return first

    return None


# ---------------------------------------------------------------------------
# 1. output.csv ni o'qish
# ---------------------------------------------------------------------------

def load_output_csv(path: str) -> dict[str, str]:
    """
    output.csv → {kalit_lotin: ma'no_lotin}
    """
    rows = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title   = row.get("Title", "").strip()
            meaning = row.get("Meaning", "").strip()
            if not title or not meaning:
                continue
            title_lat   = transliterate(title)
            meaning_lat = transliterate(meaning)
            key = clean_key(title_lat)
            if key and key not in rows:
                rows[key] = {"Title": title_lat, "Meaning": meaning_lat}
    return rows


# ---------------------------------------------------------------------------
# 2. fromexcel.csv ni o'qish
# ---------------------------------------------------------------------------

def load_fromexcel_csv(path: str) -> list[dict]:
    """
    fromexcel.csv → [{Title: lotin, Meaning: lotin}, ...]
    Faqat mazmunli, qisqa ma'noli yozuvlar.
    """
    rows = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dialect = row.get("dialect", "").strip()
            literary = row.get("literary", "").strip()

            if not dialect or not literary:
                continue

            short = extract_short_meaning(literary)
            if not short:
                continue

            key = clean_key(dialect)
            if not key:
                continue

            rows.append({"key": key, "Title": dialect, "Meaning": short})
    return rows


# ---------------------------------------------------------------------------
# 3. Birlashtirish
# ---------------------------------------------------------------------------

def merge(output_path: str, excel_path: str, backup_path: str) -> None:
    print(f"📖 output.csv o'qilmoqda: {output_path}")
    existing = load_output_csv(output_path)
    print(f"   Topildi: {len(existing)} yozuv")

    print(f"📖 fromexcel.csv o'qilmoqda: {excel_path}")
    excel_rows = load_fromexcel_csv(excel_path)
    print(f"   Topildi: {len(excel_rows)} mazmunli yozuv")

    # Zaxira nusxa
    import shutil
    shutil.copy2(output_path, backup_path)
    print(f"💾 Zaxira saqlandi: {backup_path}")

    # Yangi yozuvlarni qo'shish
    added = 0
    skipped_duplicate = 0

    for row in excel_rows:
        key = row["key"]
        if key in existing:
            skipped_duplicate += 1
            continue
        existing[key] = {"Title": row["Title"], "Meaning": row["Meaning"]}
        added += 1

    print(f"\n✅ Natija:")
    print(f"   Yangi qo'shildi:    {added}")
    print(f"   Dublikat o'tkazildi: {skipped_duplicate}")
    print(f"   Jami yozuv:         {len(existing)}")

    # output.csv ga yozish
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Title", "Meaning"])
        for data in existing.values():
            writer.writerow([data["Title"], data["Meaning"]])

    print(f"\n💾 Yangilangan output.csv saqlandi: {output_path}")


# ---------------------------------------------------------------------------
# Ishga tushirish
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_CSV):
        print(f"❌ output.csv topilmadi: {OUTPUT_CSV}")
        print("   Avval output.csv ni loyiha ildiziga ko'chiring.")
        exit(1)

    if not os.path.exists(EXCEL_CSV):
        print(f"❌ fromexcel.csv topilmadi: {EXCEL_CSV}")
        exit(1)

    merge(OUTPUT_CSV, EXCEL_CSV, BACKUP_CSV)
