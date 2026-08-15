# Source: IFCT 2017 dataset (nodef/ifct2017)

Files in this directory are copied, untouched, from:
https://github.com/nodef/ifct2017 (commit as of 2026-08-15).

Underlying nutrient data is from *Indian Food Composition Tables 2017*,
published by the National Institute of Nutrition (ICMR-NIN), Hyderabad.

**License: AGPL-3.0** (see `LICENSE` in this directory). This is a strong
copyleft license. Bundling this data into DalGains has implications for
what license the rest of this repository can use, especially if the app
is ever run as a network service. Review this before choosing a license
for the DalGains repository or distributing it beyond local/family use.

## Files

- `compositions.csv` — nutrient values per 100g edible portion for 542
  foods. `enerc` (energy) is in **kJ**, not kcal — convert by dividing by
  4.184. Macronutrient columns (`protcnt`, `fatce`, `choavldf`, `fibtg`)
  are in grams. Each nutrient column has a paired `<col>_e` uncertainty
  column.
- `codes.csv` — alternate/regional name → food code lookup.
- `descriptions.csv` — food code → local-language names (raw semicolon
  separated text per description), scientific name, food group.
- `columns.csv` — nutrient column code → human-readable name/tags.
- `representations.csv` — nutrient column code → unit and scale factor.
- `groups.csv` — food group code → group name.
