import re
import csv

with open("ocr_natija.txt", "r", encoding="utf-8") as f:
    text = f.read()

results = []
seen = set()

for line in text.split('\n'):
    line = line.strip()
    m = re.search(r'\[([^\]]+)\]\s*[–—-]\s*(.+)', line)
    if not m:
        continue
    
    xorazm = m.group(1).strip()
    tarjima_full = m.group(2).strip()
    
    uzbek = re.split(r'[,،;]', tarjima_full)[0].strip()
    uzbek = re.split(r'\(', uzbek)[0].strip()
    
    if not xorazm or not uzbek:
        continue
    
    xorazm_variants = [x.strip() for x in xorazm.split(',')]
    
    for variant in xorazm_variants:
        if not variant or variant.lower() in seen:
            continue
        seen.add(variant.lower())
        results.append((variant, uzbek))

with open("/mnt/user-data/outputs/lugat.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["xorazmcha", "o'zbekcha"])
    for row in results:
        writer.writerow(row)

print(f"Jami: {len(results)} so'z")
for r in results[:25]:
    print(r)