from bs4 import BeautifulSoup
import csv

# --- 1. Kirill → Lotin lug‘ati ---
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


# --- 2. HTML o‘qish ---
with open("input.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
items = soup.find_all("div", class_="item")

# --- 3. CSV yozish ---
with open("output_latin.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Title", "Meaning"])
    
    for item in items:
        title = item.find("div", class_="item__title").get_text(strip=True)
        meaning = item.find("div", class_="item__meaning").get_text()
        
        meaning = " ".join(meaning.split())  # newline tozalash
        
        # 🔹 Transliteration
        title = transliterate(title)
        meaning = transliterate(meaning)
        
        writer.writerow([title, meaning])

print("Tayyor: output_latin.csv yaratildi.")