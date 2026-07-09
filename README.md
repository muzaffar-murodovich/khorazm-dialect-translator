# Khorezm Dialect → Standard Uzbek Translator

A dictionary-based translation tool that converts text written in the **Khorezm dialect** into **standard literary Uzbek**, built on a lexicon I collected, cleaned, and analyzed myself.

> This was my bachelor's graduation project (Tashkent University of Information Technologies, 2026).

## The problem

The Khorezm dialect differs significantly from standard Uzbek — in vocabulary, phonetics, and everyday expressions. There was no publicly available resource that maps Khorezm dialect words to their literary equivalents, and no tool to convert dialect text automatically.

## What I built

The core of this project is not the replacement algorithm — it's the **dataset**. No Khorezm–Uzbek dictionary existed in machine-readable form, so I built one:

**1. Data mining.** Collected dialect words and expressions from web sources, digitized books, and regional texts.

**2. Data cleaning.** Normalized spelling variants, removed duplicates, resolved conflicting entries, and unified the script (Latin Uzbek).

**3. Data analysis.** Analyzed the cleaned lexicon with Pandas: frequency distributions, ambiguous mappings (one dialect word → multiple literary meanings), and coverage estimates against sample dialect texts.

**4. Translation engine.** A rule-based find-and-replace engine that applies the lexicon to input text, handling word boundaries and longest-match-first replacement so that multi-word expressions are translated before their parts.

## Example

| Khorezm dialect (input) | Standard Uzbek (output) |
|---|---|
| borina shukir | boriga shukur |
| galdim | keldim |
| Bugin meymon galdi. Anam baqqa bilan eron tayyorladi, doyim bozordan gashir oldi. Men giyimimni gizlap, oʻyga girdim. Goʻzim bilan goʻrdim, dasturxon tayyor edi. | Bugun mehmon keldi. Onam sut bilan ayron tayyorladi, togʻam bozordan sabzi oldi. Men kiyimimni olib, uyga kirdim. Koʻzim bilan koʻrdim, dasturxon tayyor edi.


## Dataset

- **~2581 entries** dialect → literary mappings
- Format: .csv
- Sources: web texts, digitized books, regional publications

## Tech stack

`Python` · `Pandas` · rule-based matching

## Limitations & future work

- Dictionary lookup can't resolve context-dependent ambiguity — a word with multiple literary equivalents is currently mapped to its most frequent one
- Grammar-level differences (suffixes, verb forms) are only partially covered
- **Natural next step:** the collected lexicon is a ready-made parallel dataset for fine-tuning a seq2seq / LLM-based translator — turning this from a rule-based tool into a proper NLP system

## Why this project matters

Low-resource language work is mostly a *data* problem, not a modeling problem. This project is an end-to-end example of that: sourcing raw data where none existed, cleaning it into a usable dataset, analyzing it, and shipping a working tool on top of it.