import csv
import re
import os

# ---------------------------------------------------------------------------
# 1. Kirill → Lotin transliteratsiya
# ---------------------------------------------------------------------------
translit_map = {
    "А": "A", "а": "a", "Б": "B", "б": "b", "В": "V", "в": "v",
    "Г": "G", "г": "g", "Д": "D", "д": "d", "Е": "E", "е": "e",
    "Ё": "Yo", "ё": "yo", "Ж": "J", "ж": "j", "З": "Z", "з": "z",
    "И": "I", "и": "i", "Й": "Y", "й": "y", "К": "K", "к": "k",
    "Л": "L", "л": "l", "М": "M", "м": "m", "Н": "N", "н": "n",
    "О": "O", "о": "o", "П": "P", "п": "p", "Р": "R", "р": "r",
    "С": "S", "с": "s", "Т": "T", "т": "t", "У": "U", "у": "u",
    "Ф": "F", "ф": "f", "Х": "X", "х": "x", "Ц": "Ts", "ц": "ts",
    "Ч": "Ch", "ч": "ch", "Ш": "Sh", "ш": "sh", "Щ": "Sh", "щ": "sh",
    "Ъ": "", "ъ": "", "Ь": "", "ь": "", "Э": "E", "э": "e",
    "Ю": "Yu", "ю": "yu", "Я": "Ya", "я": "ya",
    "Ў": "Oʻ", "ў": "oʻ", "Қ": "Q", "қ": "q",
    "Ғ": "Gʻ", "ғ": "gʻ", "Ҳ": "H", "ҳ": "h",
}


def transliterate(text: str) -> str:
    return "".join(translit_map.get(ch, ch) for ch in text)


# ---------------------------------------------------------------------------
# 2. Umumiy nom suffikslari (kelishik, koʻplik)
# ---------------------------------------------------------------------------
SUFFIXES = [
    "larning", "lardan", "larga", "larni", "larda",
    "ning", "dan", "dagi", "dek", "day", "ga", "da", "ni",
    "ingiz", "imiz", "lari", "gina",
    "lar", "ing", "im",
]

# ---------------------------------------------------------------------------
# 3. Fe'l morfologiyasi
# ---------------------------------------------------------------------------

# 3a. Sheva fe'l suffikslari → adabiy fe'l suffikslari
# Uzundan qisqaga tartibda (avval uzunini sinab koʻrish)
VERB_SUFFIX_MAP: dict[str, str] = {
    # Koʻplik shaxs shakllari
    "moqdalar": "moqdalar",
    "dilar":    "dilar",
    # Hozirgi-kelasi zamon
    "avdir":    "yotir",     # kelayotir (davomiy)
    "adir":     "yotir",
    "aman":     "moqman",    # 1-shaxs birlik
    "asan":     "moqsan",    # 2-shaxs birlik
    "amiz":     "moqmiz",    # 1-shaxs koʻplik
    "asiz":     "moqsiz",    # 2-shaxs koʻplik
    "alar":     "moqdalar",  # 3-shaxs koʻplik
    "adi":      "moqda",     # 3-shaxs birlik
    # Oʻtgan zamon
    "dilar":    "dilar",
    "ding":     "ding",
    "dik":      "dik",
    "diz":      "diz",
    "dim":      "dim",
    "di":       "di",
    # Buyruq mayli
    "gʼin":    "gin",
    "gin":      "gin",
    # Shart mayli
    "sagina":   "sangchi",
    "sang":     "sang",
    "sam":      "sam",
    "sa":       "sa",
    # Sifatdosh / ravishdosh
    "gʼan":    "gan",
    "magan":    "magan",
    "gan":      "gan",
    "may":      "may",
    "ib":       "ib",
    # Inkor
    "ma":       "ma",
    # Infinitiv
    "maq":      "moq",
    "mak":      "moq",
    "mәk":      "moq",
    # Qisqa ravishdosh
    "b":        "b",
}

# Suffikslarni uzunlikka qarab tartiblash (notoʻgʻri oʻqilishni oldini olish)
_VERB_SUFFIXES_SORTED = sorted(VERB_SUFFIX_MAP.keys(), key=len, reverse=True)


# 3b. Sheva fe'l ildizlari → adabiy fe'l ildizlari
VERB_ROOT_MAP: dict[str, str] = {
    # Asosiy harakat fe'llari (qoʻlda)
    "gal":      "kel",       # galaman → kelmoqman
    "gat":      "ket",       # gataman → ketmoqman
    "bar":      "bor",       # barmaq → bormoq

    "ayr":      "ayir",      # ayirmaq → ayirmoq
    "arala":    "yarash",    # aralamaq → yarashtirmoq
    "art":      "tozala",    # aritmoq → tozalamoq
    "basr":     "bosir",     # basirmaq → bostirmoq
    "dag":      "tarqa",     # dagilmaq → tarqalmoq
    "dad":      "tati",      # dadimaq → tatimoq
    "dar":      "komakla",   # darimaq → koʻmaklashmoq
    "dasla":    "qir",       # daslamaq → qirmoq
    "daya":     "suya",      # dayamaq → suyamoq
    "dayn":     "siypan",    # dayinmoq → siypanmoq
    "dog":      "tug",       # dogmaq → tugʻmoq
    "doq":      "sovqot",    # doqmaq → sovqotmoq
    "dun":      "tin",       # dunmaq → tinmoq
    "dunt":     "tinit",     # duntmaq → tinitmoq
    "dura":     "urchi",     # duramaq → urchimoq
    "dushiq":   "duch kel",  # dushiqmaq → duch kelmoq
    "dөn":      "ayni",      # donmak → aynimoq
    "dөrәt":    "yarat",     # doratmak → yaratmoq
    "dөv":      "tuy",       # dovmak → tuymoq
    "gүdүrlә":  "guldira",   # gudurlamak → guldiramoq
    "gүlisha":  "kulish",    # gulishamak → kulishmoq
    "gөy":      "kuy",       # goymak → kuymoq
    "kәp":      "quri",      # kapmak → qurimoq
    "kәvi":     "qaqra",     # kavimak → qaqramoq
    "saga":     "sogay",     # sagalmaq → sogʻaymoq
    "sal":      "chayqa",    # sallanmaq → chayqalmoq
    "salbra":   "shalvira",  # salbiramaq → shalviramoq
    "sandra":   "valdira",   # sandramaq → valdiramoq
    "sap":      "ula",       # sapmaq → ulamoq
    "sara":     "sargay",    # saralmoq → sargʻaymoq
    "sav":      "sov",       # savmaq → sovmoq
    "say":      "sava",      # saymaq → savamoq
    "saz":      "oz",        # sazmaq → ozmoq
    "suvar":    "sugor",     # suvarmaq → sugʻormoq
    "sүmür":    "shimir",    # sumurмак → shimirmoq
    "sүndik":   "kokil",     # sundikmak → koʻkilmoq
    "sүrrә":    "sudra",     # surramak → sudramoq
    "sүy":      "sev",       # suymak → sevmoq
    "sүyrә":    "sudra",     # suyrамак → sudramoq
    "sөv":      "sev",       # sovmak → sevmoq
    "sөvүn":    "suyun",     # sovunmak → suyunmoq
    "sөylә":    "sozla",     # soylamas → sozlamoq
    "yagla":    "yigla",     # yaglamaq → yigʻlamoq
    "yagna":    "yig",       # yagnamaq → yigʻmoq
    "yallqa":   "komakla",   # yalliqamaq → koʻmaklashmoq
    "yalpash":  "agna",      # yalpashmaq → agʻnamoq
    "yantash":  "yondash",   # yantashmaq → yondashmoq
    "yaq":      "yangli",    # yaqilmaq → yanglishmoq
    "yar":      "yolchi",    # yarimaq → yolchimoq
    "yatr":     "yotqiz",    # yatirmaq → yotqizmoq
    "yayna":    "yayra",     # yaynamaq → yayramoq
    "yaz":      "yoz",       # yazmaq → yozmoq
    "yazdr":    "boshat",    # yazdirmaq → boʻshatmoq
    "yeg":      "hayda",     # yegmak → haydamoq
    "yegla":    "yigla",     # yeglamaq → yigʻlamoq
    "yejәsh":   "ochakish",  # yejashmak → oʻchakishmoq
    "yench":    "yanch",     # yenchmak → yanchmoq
    "yeqna":    "yig",       # yeqnamaq → yigʻmoq
    "yesh":     "esh",       # yeshmak → eshmoq
    "yet":      "yetakla",   # yetmak → yetaklamoq
    "yetir":    "yetkaz",    # yetirmak → yetkazmoq
    "yetәsh":   "yetak",     # yetashmak → yetaklashmoq
    "yey":      "eg",        # yeymak → egmoq
    "yeyi":     "yoz",       # yeyilmak → yozilmoq
    "yeyәr":    "ergash",    # yeyermak → ergashmoq
    "ygir":     "burish",    # ygirmaq → burishtirmoq
    "yigna":    "yeng",      # yignamaq → yengmoq
    "yili":     "jil",       # yilimak → jilmoq
    "yiq":      "yiqit",     # yiqmaq → yiqitmoq
    "yuvan":    "yupan",     # yuvanmaq → yupanmoq
    "yүqlә":    "rivojlan",  # yuqlamas → rivojlanmoq
    "yүri":     "yur",       # yurimas → yurmoq
    "yүyir":    "yugur",     # yuyirmas → yugurmoq
    "yүzikish": "uchrash",   # yuzikishmak → uchrashmoq
}


def _normalize(word: str) -> str:
    """
    Sheva yozuvida uchraydigan variant belgilarni standartlashtiradi.
    Masalan: ø → ө, ü → ү, va hokazo.
    """
    table = str.maketrans({
        "ø": "ө", "ö": "ө",
        "ü": "ү", "ú": "ү",
        "ʼ": "", "ʻ": "", "'": "",
        "\u02BC": "",
    })
    return word.translate(table)


def strip_verb_suffix(word: str) -> tuple[str, str] | tuple[None, None]:
    """
    Soʻzdan sheva fe'l suffiksini ajratadi.
    Qaytaradi: (ildiz, suffix) yoki (None, None)
    """
    w = _normalize(word.lower())
    for suf in _VERB_SUFFIXES_SORTED:
        if w.endswith(suf) and len(w) > len(suf) + 1:
            root = w[: -len(suf)]
            if len(root) >= 2:
                return root, suf
    return None, None


def translate_verb(word: str) -> str | None:
    """
    Sheva fe'lini morfologik tahlil qilib adabiy shaklga oʻtkazadi.
    1. Suffiksni ajratadi
    2. Sheva ildizini adabiy ildizga almashtiradi
    3. Sheva suffiksini adabiy suffiksga almashtiradi
    4. Birlashtiradi
    Agar tarjima topilmasa None qaytaradi.
    """
    normalized = _normalize(word.lower())
    root, sheva_suf = strip_verb_suffix(normalized)
    if root is None:
        # Suffikssiz — toʻliq soʻzni ildiz sifatida qidirish
        adabiy_root = VERB_ROOT_MAP.get(normalized)
        return adabiy_root if adabiy_root else None

    adabiy_root = VERB_ROOT_MAP.get(root)
    if adabiy_root is None:
        return None

    adabiy_suf = VERB_SUFFIX_MAP.get(sheva_suf, sheva_suf)
    return adabiy_root + adabiy_suf


# ---------------------------------------------------------------------------
# 4. Lugʻat yuklash
# ---------------------------------------------------------------------------

def _extract_short_meaning(meaning_latin: str) -> str | None:
    """
    Meaning matnidan tarjimaga yaraqli qisqa alternativni ajratib oladi.
    - <= 6 soʻz boʻlsa, toʻliq ishlatiladi
    - Uzun boʻlsa, vergul/nuqtagacha boʻlgan birinchi qism tekshiriladi (<=3 soʻz)
    - Aks holda None qaytaradi
    """
    meaning = meaning_latin.strip()
    if not meaning or meaning.lower() == "nan":
        return None

    words = meaning.split()
    if len(words) <= 6:
        # Koʻp ma'noli boʻlsa birinchi qismni ol: "soʻz1; soʻz2" → "soʻz1"
        for sep in [";", ","]:
            idx = meaning.find(sep)
            if idx != -1:
                first = meaning[:idx].strip()
                if first:
                    return first
        return meaning

    for sep in [";", ",", "."]:
        idx = meaning.find(sep)
        if idx != -1:
            first_part = meaning[:idx].strip()
            if len(first_part.split()) <= 3:
                return first_part

    return None


def _insert_into_dicts(
    key: str,
    short_meaning: str,
    single_dict: dict,
    phrase_dict: dict,
) -> None:
    """
    Kalitni toʻgʻri lugʻatga qoʻshadi (agar mavjud boʻlmasa).
    Ma'no doimo kichik harfda saqlanadi — _match_case keyin
    original soʻz registriga qarab bosh harf qoʻyadi.
    """
    key = re.sub(r"\(.*?\)", "", key).strip()
    if not key:
        return
    target = phrase_dict if " " in key else single_dict
    if key not in target:
        target[key] = short_meaning.lower()


def load_dictionary(csv_path: str) -> tuple[dict, dict]:
    """
    output.csv faylni yuklaydi (Title, Meaning ustunlari).
    Kirill yozuvlari avtomatik transliteratsiya qilinadi.
    Qaytaradi: (single_dict, phrase_dict)
    """
    single_dict: dict[str, str] = {}
    phrase_dict: dict[str, str] = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_title   = row.get("Title", "").strip()
            raw_meaning = row.get("Meaning", "").strip()

            if not raw_title or not raw_meaning:
                continue

            title_lat   = transliterate(raw_title)
            meaning_lat = transliterate(raw_meaning)

            short = _extract_short_meaning(meaning_lat)
            if not short:
                continue

            key = title_lat.lower().strip()
            _insert_into_dicts(key, short, single_dict, phrase_dict)

    return single_dict, phrase_dict


def load_fromexcel(csv_path: str, single_dict: dict, phrase_dict: dict) -> int:
    """
    fromexcel.csv dan yangi soʻzlarni mavjud lugʻatga qoʻshadi.
    (dialect, literary ustunlari, Lotin yozuvi)

    output.csv dagi yozuvlar USTUVOR — faqat yangi kalit qoʻshiladi.
    Qaytaradi: qoʻshilgan yangi yozuvlar soni.
    """
    added = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dialect  = row.get("dialect", "").strip()
            literary = row.get("literary", "").strip()

            if not dialect or not literary:
                continue
            if literary.lower() in ("nan", "mavjud emas", "not attested"):
                continue

            short = _extract_short_meaning(literary)
            if not short:
                continue

            key = re.sub(r"\s+", " ", dialect.lower().strip())
            _insert_into_dicts(key, short, single_dict, phrase_dict)
            added += 1

    return added


# ---------------------------------------------------------------------------
# 5. Yordamchi funksiyalar
# ---------------------------------------------------------------------------

def _match_case(original: str, replacement: str) -> str:
    """Asl soʻz registrini tarjimaga koʻchiradi."""
    if not replacement:
        return replacement
    if original.isupper():
        return replacement.upper()
    if original[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _strip_suffix(word: str) -> list[tuple[str, str]]:
    """
    Nom va boshqa soʻz turkumlari uchun qoʻshimcha qirqish.
    Qaytaradi: [(ildiz, qoʻshimcha), ...]
    """
    candidates = []
    lower = word.lower()
    for suffix in SUFFIXES:
        if lower.endswith(suffix) and len(lower) > len(suffix) + 2:
            root = lower[: -len(suffix)]
            candidates.append((root, suffix))
    return candidates


# ---------------------------------------------------------------------------
# 6. Tokenizatsiya
# ---------------------------------------------------------------------------
_TOKEN_RE = re.compile(r"([\w'ʻʼ\u02BC]+|[^\w'ʻʼ\u02BC]+)", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


# ---------------------------------------------------------------------------
# 7. Asosiy tarjima funksiyasi
# ---------------------------------------------------------------------------

def translate(
    text: str,
    single_dict: dict,
    phrase_dict: dict,
) -> tuple[str, int, int]:
    """
    Matnni tarjima qiladi.

    Tarjima tartibi:
      1. Koʻp soʻzli iboralar (phrase_dict, 3 soʻzgacha)
      2. Aniq soʻz (single_dict)
      3. Fe'l morfologik tahlil (VERB_ROOT_MAP + VERB_SUFFIX_MAP)
      4. Nom suffiksi qirqib ildizni qidirish
      5. Oʻzgartirilmay qoldiriladi

    Qaytaradi: (tarjima_matni, tarjima_qilingan_soni, jami_soʻzlar)
    """
    tokens = tokenize(text)
    result = []
    translated_count = 0
    total_words = 0

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Tinish belgisi yoki boʻsh joy
        if not token.strip() or not re.search(r"\w", token):
            result.append(token)
            i += 1
            continue

        total_words += 1
        token_lower = token.lower()

        # --- 1. Koʻp soʻzli iboralar (3 va 2 soʻz) ---
        found_phrase = False
        for phrase_len in (3, 2):
            end_idx = i + phrase_len * 2 - 1
            if end_idx <= len(tokens):
                phrase_tokens = tokens[i:end_idx]
                phrase_words = [t for t in phrase_tokens if re.search(r"\w", t)]
                if len(phrase_words) == phrase_len:
                    phrase_key = " ".join(w.lower() for w in phrase_words)
                    if phrase_key in phrase_dict:
                        replacement = _match_case(phrase_words[0], phrase_dict[phrase_key])
                        result.append(replacement)
                        translated_count += 1
                        i += phrase_len * 2 - 1
                        found_phrase = True
                        break

        if found_phrase:
            continue

        # --- 2. Aniq soʻz mosligini tekshirish ---
        if token_lower in single_dict:
            result.append(_match_case(token, single_dict[token_lower]))
            translated_count += 1
            i += 1
            continue

        # --- 3. Fe'l morfologik tahlil ---
        verb_translation = translate_verb(token_lower)
        if verb_translation:
            result.append(_match_case(token, verb_translation))
            translated_count += 1
            i += 1
            continue

        # --- 4. Nom suffiksi qirqib ildizni qidirish ---
        suffix_found = False
        for root, suffix in _strip_suffix(token):
            if root in single_dict:
                base = single_dict[root]
                # Adabiy ildiz + original sheva suffiksi
                # (kelishik suffikslari oʻzbek tilida ham bir xil)
                result.append(_match_case(token, base) + suffix)
                translated_count += 1
                suffix_found = True
                break
            # Fe'l ildizini ham tekshirib koʻrish
            verb_root_trans = VERB_ROOT_MAP.get(root)
            if verb_root_trans:
                result.append(_match_case(token, verb_root_trans) + suffix)
                translated_count += 1
                suffix_found = True
                break

        if suffix_found:
            i += 1
            continue

        # --- 5. Topilmadi ---
        result.append(token)
        i += 1

    return "".join(result), translated_count, total_words


# ---------------------------------------------------------------------------
# 8. Lugʻatni bir marta yuklash
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_CSV_PATH = os.path.join(_BASE_DIR, "data", "output.csv")

single_dict, phrase_dict = load_dictionary(_CSV_PATH)
DICT_SIZE = len(single_dict) + len(phrase_dict)