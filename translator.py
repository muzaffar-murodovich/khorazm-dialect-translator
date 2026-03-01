import csv
import re
import os

# --- Kirill → Lotin lug'ati (scraper.py dan olingan) ---
translit_map = {
    "А": "A", "а": "a",
    "Б": "B", "б": "b",
    "В": "V", "в": "v",
    "Г": "G", "г": "g",
    "Д": "D", "д": "d",
    "Е": "E", "е": "e",
    "Ё": "Yo", "ё": "yo",
    "Ж": "J", "ж": "j",
    "З": "Z", "з": "z",
    "И": "I", "и": "i",
    "Й": "Y", "й": "y",
    "К": "K", "к": "k",
    "Л": "L", "л": "l",
    "М": "M", "м": "m",
    "Н": "N", "н": "n",
    "О": "O", "о": "o",
    "П": "P", "п": "p",
    "Р": "R", "р": "r",
    "С": "S", "с": "s",
    "Т": "T", "т": "t",
    "У": "U", "у": "u",
    "Ф": "F", "ф": "f",
    "Х": "X", "х": "x",
    "Ц": "Ts", "ц": "ts",
    "Ч": "Ch", "ч": "ch",
    "Ш": "Sh", "ш": "sh",
    "Щ": "Sh", "щ": "sh",
    "Ъ": "", "ъ": "",
    "Ь": "", "ь": "",
    "Э": "E", "э": "e",
    "Ю": "Yu", "ю": "yu",
    "Я": "Ya", "я": "ya",
    "Ў": "Oʻ", "ў": "oʻ",
    "Қ": "Q", "қ": "q",
    "Ғ": "Gʻ", "ғ": "gʻ",
    "Ҳ": "H", "ҳ": "h",
}


def transliterate(text):
    return "".join(translit_map.get(char, char) for char in text)


# O'zbek tili qo'shimchalari (uzundan qisqaga — avval uzunini tekshirish)
SUFFIXES = [
    "larning", "lardan", "larga", "larni", "larda",
    "ning", "dan", "dagi", "dek", "day", "ga", "da", "ni",
    "ingiz", "imiz", "lari", "gina",
    "lar", "ing", "im",
]


def _extract_short_meaning(meaning_latin: str) -> str | None:
    """
    Meaning matnidan tarjimaga yaraqli qisqa alternativni ajratib oladi.
    - <= 6 so'z bo'lsa, to'liq ishlatiladi
    - Uzun bo'lsa, vergul yoki nuqtagacha bo'lgan birinchi qism tekshiriladi
    - Agar birinchi qism <= 3 so'z bo'lsa, uni qaytaradi
    - Aks holda None qaytaradi (tarjimada ishlatilmaydi)
    """
    meaning = meaning_latin.strip()
    if not meaning or meaning.lower() == "nan":
        return None

    words = meaning.split()
    if len(words) <= 6:
        return meaning

    # Vergul yoki nuqtaga qadar bo'lgan birinchi qismni olish
    for sep in [",", "."]:
        idx = meaning.find(sep)
        if idx != -1:
            first_part = meaning[:idx].strip()
            if len(first_part.split()) <= 3:
                return first_part

    return None


def load_dictionary(csv_path: str) -> tuple[dict, dict]:
    """
    CSV faylni yuklaydi va ikkita lug'at qaytaradi:
    - single_dict: {lowercase_word: translation}
    - phrase_dict: {lowercase_phrase: translation}  (ko'p so'zli iboralar)
    """
    single_dict: dict[str, str] = {}
    phrase_dict: dict[str, str] = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_title = row.get("Title", "").strip()
            raw_meaning = row.get("Meaning", "").strip()

            if not raw_title or not raw_meaning:
                continue

            title_lat = transliterate(raw_title)
            meaning_lat = transliterate(raw_meaning)

            short = _extract_short_meaning(meaning_lat)
            if not short:
                continue

            key = title_lat.lower().strip()
            if not key:
                continue

            # Qavslarni tozalash: "Azib ichar (variant)" → "azib ichar"
            key = re.sub(r"\(.*?\)", "", key).strip()

            if " " in key:
                phrase_dict[key] = short
            else:
                single_dict[key] = short

    return single_dict, phrase_dict


def _match_case(original: str, replacement: str) -> str:
    """Asl so'z registrini tarjimaga ko'chiradi."""
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _strip_suffix(word: str) -> list[str]:
    """So'zdan qo'shimchalarni qirqib, mumkin bo'lgan ildizlarni qaytaradi."""
    candidates = []
    lower = word.lower()
    for suffix in SUFFIXES:
        if lower.endswith(suffix) and len(lower) > len(suffix) + 2:
            root = lower[: -len(suffix)]
            candidates.append((root, suffix))
    return candidates


# --- Tokenizatsiya: so'zlar va tinish belgilarini alohida saqlash ---
_TOKEN_RE = re.compile(r"([\w'ʻʼ\u02BC]+|[^\w'ʻʼ\u02BC]+)", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def translate(text: str, single_dict: dict, phrase_dict: dict) -> tuple[str, int, int]:
    """
    Matnni tarjima qiladi.
    Qaytaradi: (translated_text, translated_count, total_word_count)
    """
    tokens = tokenize(text)
    result = []
    translated_count = 0
    total_words = 0

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Tinish belgisi yoki bo'sh joy — o'zgartirmay qo'shish
        if not token.strip() or not re.search(r"\w", token):
            result.append(token)
            i += 1
            continue

        total_words += 1
        token_lower = token.lower()

        # 1. Ko'p so'zli iboralarni tekshirish (3 so'zgacha)
        found_phrase = False
        for phrase_len in (3, 2):
            if i + (phrase_len * 2 - 1) <= len(tokens):
                # phrase_len ta so'zni olib, oradagi bo'shliqlarni ham hisobga olish
                phrase_tokens = tokens[i : i + phrase_len * 2 - 1]
                phrase_words = [t for t in phrase_tokens if re.search(r"\w", t)]
                if len(phrase_words) == phrase_len:
                    phrase_key = " ".join(w.lower() for w in phrase_words)
                    if phrase_key in phrase_dict:
                        replacement = phrase_dict[phrase_key]
                        replacement = _match_case(phrase_words[0], replacement)
                        result.append(replacement)
                        translated_count += 1
                        i += phrase_len * 2 - 1
                        found_phrase = True
                        break

        if found_phrase:
            continue

        # 2. Alohida so'zni tekshirish
        if token_lower in single_dict:
            replacement = _match_case(token, single_dict[token_lower])
            result.append(replacement)
            translated_count += 1
            i += 1
            continue

        # 3. Qo'shimchani qirqib ildizni qidirish
        suffix_found = False
        for root, suffix in _strip_suffix(token):
            if root in single_dict:
                base_translation = single_dict[root]
                # Ildiz tarjima qilinadi, qo'shimcha o'zgartirilmay qo'shiladi
                replacement = _match_case(token, base_translation) + suffix
                result.append(replacement)
                translated_count += 1
                suffix_found = True
                break

        if suffix_found:
            i += 1
            continue

        # 4. Topilmadi — o'zgartirilmay qoldiriladi
        result.append(token)
        i += 1

    return "".join(result), translated_count, total_words


# --- Lug'atni bir marta yuklash ---
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CSV_PATH = os.path.join(_BASE_DIR, "output.csv")

single_dict, phrase_dict = load_dictionary(_CSV_PATH)
DICT_SIZE = len(single_dict) + len(phrase_dict)
