#!/usr/bin/env python3
"""
CSV faylni tozalash skripti.
  - Ortiqcha (takroriy) qatorlarni o'chiradi
  - Qatorlarni alifbo tartibida saralaydi
  - Barcha matnlarni lower case qiladi

Ishlatish:
    python csv_clean.py input.csv
    python csv_clean.py input.csv -o natija.csv
    python csv_clean.py input.csv --sort-column Title
    python csv_clean.py input.csv --no-lowercase
"""

import csv
import argparse
import sys
from pathlib import Path


def clean_csv(
    input_path: str,
    output_path: str | None = None,
    sort_column: str | None = None,
    lowercase: bool = True,
) -> None:
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Xato: '{input_path}' fayl topilmadi.", file=sys.stderr)
        sys.exit(1)

    # Chiqish fayl nomi
    if output_path is None:
        output_path = input_file.stem + "_clean" + input_file.suffix

    # CSV o'qish
    with open(input_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("Xato: CSV faylda ustun nomlari topilmadi.", file=sys.stderr)
            sys.exit(1)
        rows = list(reader)

    total_before = len(rows)

    # 1. Barcha qiymatlarni lower case qilish
    if lowercase:
        rows = [
            {k: v.lower().strip() for k, v in row.items()}
            for row in rows
        ]
    else:
        rows = [
            {k: v.strip() for k, v in row.items()}
            for row in rows
        ]

    # 2. Takroriy qatorlarni o'chirish
    seen = set()
    unique_rows = []
    for row in rows:
        key = tuple(row.values())
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)

    duplicates_removed = total_before - len(unique_rows)

    # 3. Alifbo tartibida saralash
    if sort_column:
        if sort_column not in fieldnames and sort_column.lower() not in [f.lower() for f in fieldnames]:
            print(f"Ogohlantirish: '{sort_column}' ustuni topilmadi. Birinchi ustun bo'yicha saralamoqda.", file=sys.stderr)
            sort_column = fieldnames[0]
        # Case-insensitive ustun nomi moslashtirish
        actual_col = next((f for f in fieldnames if f.lower() == sort_column.lower()), fieldnames[0])
    else:
        actual_col = fieldnames[0]

    unique_rows.sort(key=lambda r: r.get(actual_col, ""))

    # CSV yozish
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_rows)

    # Hisobot
    print("=" * 45)
    print("CSV tozalash hisoboti")
    print("=" * 45)
    print(f"Kirish fayl:          {input_path}")
    print(f"Chiqish fayl:         {output_path}")
    print(f"Jami qatorlar:        {total_before}")
    print(f"O'chirilgan takrorlar: {duplicates_removed}")
    print(f"Natija qatorlar:      {len(unique_rows)}")
    print(f"Saralash ustuni:      '{actual_col}'")
    print(f"Lower case:           {'ha' if lowercase else 'yo'q'}")
    print("=" * 45)


def main():
    parser = argparse.ArgumentParser(
        description="CSV faylni tozalash: takrorlar, saralash, lower case"
    )
    parser.add_argument("input", help="Kirish CSV fayl yo'li")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Chiqish CSV fayl yo'li (default: input_clean.csv)"
    )
    parser.add_argument(
        "--sort-column",
        default=None,
        metavar="USTUN",
        help="Saralash ustuni nomi (default: birinchi ustun)"
    )
    parser.add_argument(
        "--no-lowercase",
        action="store_true",
        help="Lower case qilmaslik"
    )

    args = parser.parse_args()

    clean_csv(
        input_path=args.input,
        output_path=args.output,
        sort_column=args.sort_column,
        lowercase=not args.no_lowercase,
    )


if __name__ == "__main__":
    main()
