"""
data/output.csv lug'atini tozalash va standartlashtirish skripti.
Natija: data/output_clean.csv
"""

import csv
import re
import sys
import os

# translator.py dan translit_map va transliterate ni import qilish
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translator import translit_map



# translit_map da yo'q, lekin CSV da uchraydigan qo'shimcha Kirill harflari
extra_translit = {
    "ы": "i",
    "Ы": "I",
    "ң": "ng",
    "Ң": "Ng",
}

_full_map = {**translit_map, **extra_translit}


def transliterate(text: str) -> str:
    """Kirill → Lotin transliteratsiya. Allaqachon Lotinda bo'lgan belgilar o'zgarmaydi."""
    return "".join(_full_map.get(ch, ch) for ch in text)


def has_cyrillic(text: str) -> bool:
    """Matnda Kirill harflari borligini tekshiradi."""
    return bool(re.search(r"[А-Яа-яЁёЎўҚқҒғҲҳыЫңҢ]", text))


# Geografik izohlar — o'chirilishi kerak
GEO_PATTERNS = [
    r"\bmahalla\s+nomi\b",
    r"\bqishloq\s+nomi\b",
    r"\bkanal\s+nomi\b",
    r"\bkoʻcha\s+nomi\b",
    r"\bshaxar\s+nomi\b",
    r"\bdaryo\s+nomi\b",
    r"\bguzar\s+nomi\b",
    # Kirill variantlari ham (transliteratsiyadan oldin tekshirish uchun)
    r"\bмаҳалла\s+номи\b",
    r"\bқишлоқ\s+номи\b",
    r"\bканал\s+номи\b",
]

# Tashlab yuboriladigan qiymatlar
SKIP_VALUES = {"mavjud emas", "not attested", "nan"}


def is_geo_annotation(text: str) -> bool:
    """Matn geografik izoh ekanligini tekshiradi."""
    lower = text.lower()
    for pat in GEO_PATTERNS:
        if re.search(pat, lower):
            return True
    return False


def clean_numbered(text: str) -> str:
    """
    Raqam bilan boshlangan matndan faqat birinchi qismni oladi.
    "1. Chiqindi suv ketadigan chuqurcha. 2. O'tgan davr..." → "Chiqindi suv ketadigan chuqurcha"
    "1. buzuq. Fohisha" → "buzuq"
    """
    # "1. matn" shaklini tekshirish
    m = re.match(r"^\d+\.\s*(.+)", text)
    if not m:
        return text

    first_content = m.group(1).strip()

    # Keyingi raqamli qism bormi? ("2.", "3." va h.k.)
    split = re.split(r"\s*\d+\.\s*", first_content, maxsplit=1)
    if split:
        return split[0].rstrip(". ;,").strip()

    return first_content.rstrip(". ;,").strip()


def should_filter_long(text: str) -> bool:
    """
    6 so'zdan uzun VA verguldan oldingi qism ham 3 so'zdan uzun — o'chirish.
    """
    words = text.split()
    if len(words) <= 6:
        return False

    # Verguldan oldingi qismni tekshirish
    comma_idx = text.find(",")
    if comma_idx != -1:
        first_part = text[:comma_idx].strip()
        if len(first_part.split()) <= 3:
            return False  # Birinchi qismi qisqa — saqlab qolish mumkin

    return True


def extract_short_meaning(text: str) -> str | None:
    """
    Uzun izohdan qisqa tarjimani ajratib oladi.
    Agar matn 6 so'zdan uzun bo'lsa, verguldan/nuqtadan oldingi <=3 so'zlik qismni oladi.
    """
    words = text.split()
    if len(words) <= 6:
        return text

    # Vergul yoki nuqtadan oldingi qisqa qismni olish
    for sep in [",", "."]:
        idx = text.find(sep)
        if idx != -1:
            first_part = text[:idx].strip()
            if 0 < len(first_part.split()) <= 3:
                return first_part

    return None


def clean_row(title: str, meaning: str) -> tuple[str | None, str | None, str]:
    """
    Bitta qatorni tozalaydi.
    Qaytaradi: (clean_title, clean_meaning, action)
    action: "kept" | "modified" | "deleted"
    """
    # 1. Transliteratsiya
    if has_cyrillic(title):
        title = transliterate(title)
    if has_cyrillic(meaning):
        meaning = transliterate(meaning)

    # Bo'sh joy tozalash
    title = title.strip()
    meaning = meaning.strip()

    # 2. "Mavjud emas", "nan" kabi qiymatlarni o'chirish
    if meaning.lower().strip() in SKIP_VALUES:
        return None, None, "deleted"

    # 3. Geografik izohlarni o'chirish
    if is_geo_annotation(meaning):
        return None, None, "deleted"

    # 4. Raqam bilan boshlanganlarni tozalash
    original_meaning = meaning
    if re.match(r"^\d+\.\s*", meaning):
        meaning = clean_numbered(meaning)

    # 5. Uzun izohlarni filtrlash
    if should_filter_long(meaning):
        short = extract_short_meaning(meaning)
        if short:
            meaning = short
        else:
            return None, None, "deleted"

    # 6. Tozalangan ma'no bo'sh bo'lsa — o'chirish
    if not meaning.strip():
        return None, None, "deleted"

    action = "modified" if meaning != original_meaning else "kept"
    return title, meaning, action


def main():
    input_path = os.path.join(os.path.dirname(__file__), "data", "output.csv")
    output_path = os.path.join(os.path.dirname(__file__), "data", "output_clean.csv")

    kept = 0
    modified = 0
    deleted = 0
    transliterated = 0
    total = 0

    rows_out = []

    with open(input_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            raw_title = row.get("Title", "").strip()
            raw_meaning = row.get("Meaning", "").strip()

            if not raw_title or not raw_meaning:
                deleted += 1
                continue

            # Transliteratsiya sodir bo'lganini aniqlash
            had_cyrillic = has_cyrillic(raw_title) or has_cyrillic(raw_meaning)

            clean_title, clean_meaning, action = clean_row(raw_title, raw_meaning)

            if action == "deleted":
                deleted += 1
                continue

            if had_cyrillic:
                transliterated += 1
                if action == "kept":
                    action = "modified"  # transliteratsiya ham o'zgarish

            if action == "modified":
                modified += 1
            else:
                kept += 1

            rows_out.append({"Title": clean_title, "Meaning": clean_meaning})

    # Yozish
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Meaning"])
        writer.writeheader()
        writer.writerows(rows_out)

    # Hisobot
    print("=" * 50)
    print("Lug'at tozalash hisoboti")
    print("=" * 50)
    print(f"Jami qatorlar:          {total}")
    print(f"Saqlangan (o'zgarmagan): {kept}")
    print(f"O'zgartirilgan:         {modified}")
    print(f"  - Transliteratsiya:   {transliterated}")
    print(f"O'chirilgan:            {deleted}")
    print(f"Natija fayl:            {len(rows_out)} qator")
    print(f"Saqlangan joy:          {output_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
