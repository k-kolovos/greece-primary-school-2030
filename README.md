# Greece's Primary School of 2030 Is Already Born

Pupils, schools and an ageing teacher workforce: a data analysis of Greek primary education towards 2030.

**Interactive dashboard:** [Tableau Public](https://public.tableau.com/app/profile/konstantinos.kolovos5903/viz/GreecesPrimarySchoolof2030IsAlreadyBorn/Dashboard1)
**Author:** Konstantinos Kolovos — mathematician, MSc Business Analytics (AUEB)

## Key findings

1. **The pupils of 2030 are already born.** Enrolment six years ahead is determined by recorded births. Primary school pupils are projected to fall by ~14% between school years 2023/24 and 2029/30 — in every one of Greece's 13 regions.

2. **The decline is accelerating.** In 8 of 13 regions — and nationally — the projected fall for 2023/24 → 2029/30 exceeds the fall already recorded for 2017/18 → 2023/24 (−14.0% vs −11.9% nationally). Regional spread over the full twelve years: from −3% (South Aegean) to −37% (Western Macedonia).

3. **Schools shrink, they don't close.** Between 2017/18 and 2023/24, pupils in public primary schools fell 14.3% (601,527 → 515,269), classes fell 8.1% and school units fell only 3.7% (4,328 → 4,166). Average school size dropped from 139 to 124 pupils. The pace of administrative closures has since accelerated: 9 primary schools abolished and 43 downgraded for 2025/26, rising to 32 abolished and 106 downgraded for 2026/27.

4. **A fragmented network, not generous staffing.** Greece has one of the EU's lowest pupil-teacher ratios (7.4 vs EU-27 13.3, 2024) — driven by the small multi-grade school network, not by conditions in cities: average class size ranges from 12 pupils (Florina) to 19 (Athens). In Evrytania 7 in 10 primary schools are officially designated multi-grade; in central Athens, none.

5. **A retirement wave is at the door.** One in four primary teachers is already 55 or older (20,801 of 77,598). The large cohort — those born 1965–69 — has moved one full age band in five years: 22,636 were 50–54 in 2018/19; 17,973 are 55–59 today. They cross the minimum retirement age of 62 between 2027 and 2031. How fast such a cohort empties is measurable: of the 8,757 who were 55–59 in 2018/19, only 2,676 were still serving five years later.

6. **The wave has no second wave behind it.** The next age band is already 40% smaller (10,769), the one after that 60% smaller (7,207). Departures and appointments of ΠΕ70 teachers currently run roughly one to one (4,089 vs 4,750 over 2024–2026). When this cohort passes, both will fall.

*No numerical forecast of teacher departures is attempted: the two available sources — age stocks and published resignation counts — differ by roughly a factor of two, and the timing depends on years of service, which are not published. See [methodology](docs/methodology.md), section 6.5.*

## Repository structure

```
├── README.md
├── scripts/
│   └── build_datasets.py       # full ETL: Eurostat API → all p2_*.csv files
├── data/
│   ├── p2_enrolments_nuts2.csv
│   ├── p2_births_nuts3.csv
│   ├── p2_funnel_nuts2.csv          # chart 01, 02
│   ├── p2_change_ranking.csv        # chart 03
│   ├── p2_diktyo_2017_2024.csv      # chart 07
│   ├── p2_mikra_sxoleia.csv         # chart 05
│   ├── p2_oligothesia.csv
│   ├── p2_nomoi_2024_full.csv       # chart 04
│   ├── p2_nomoi_2017_2024.csv
│   ├── p2_pyramida_ilikion.csv      # chart 08
│   └── p2_teachers_55plus.csv
└── docs/
    └── methodology.md          # πλήρης μεθοδολογία, δεδομένα και περιορισμοί (Greek)
```

## Data sources

| Source | Dataset | Used for |
|---|---|---|
| Eurostat | `educ_uoe_enrp06` | Enrolments by region (NUTS 2), 2013–2024 |
| Eurostat | `demo_r_gind3` (LBIRTH) | Births by region (NUTS 3), 2000–2024 |
| Eurostat | `educ_uoe_perp01` | Teachers by age group (ISCED 1), 2013–2024 |
| Eurostat | `educ_uoe_perp04` | Pupil-teacher ratio, EU comparison |
| ELSTAT | Primary education surveys | Public/private split, definitions |
| Ministry of Education | Per-directorate files 2017/18, 2023/24 | Pupils, classes, teachers, schools by Directorate |
| data.gov.gr | `minedu_students_school` | Per-school enrolments, multi-grade designation (2019) |
| Government Gazette (ΦΕΚ) | Appointment lists 2024, 2025; allocation 2026 | Permanent appointments by branch |
| Government Gazette (ΦΕΚ) | School unit decisions 2025/26, 2026/27 | Closures, mergers, downgrades |

## Data notes

- **Year convention:** Eurostat years refer to the school year that ends — `2024` is school year 2023/24, `2030` is 2029/30.
- **Teacher headcounts** (ELSTAT/Eurostat, sourced from the MySchool platform) cover *all serving teaching staff*: permanent and substitute, public and private schools, general and special education, including staff on long absence or secondment. Private schools account for 4.9% of the total (2023/24). Age distribution by employment status is not published; the attribution of the 55+ groups predominantly to permanent staff is an inference (see methodology).
- **Break in series:** teacher data for 2013–2015 carry a Eurostat break-in-series flag and are not comparable with 2016 onwards.
- The **+13% jump in total teaching staff in 2023/24** partly reflects substitute hiring and improved registry coverage, not only permanent appointments.
- **Birth cohort window:** the six birth years matched to each school year were selected empirically by testing three alternatives against recorded enrolments 2015–2024; the chosen window (t−11 … t−6) gives a mean absolute error of 3.2%.
- The latest available figures refer to school year **2023/24**; the two intervening years have not yet been published.

## Reproducibility

```bash
python scripts/build_datasets.py
```

The script queries the Eurostat dissemination API directly (no key required) and writes all `p2_*.csv` files. Two Ministry of Education `.xlsx` files must be downloaded manually from statistics.minedu.gov.gr (the site blocks programmatic access); filenames are documented in the script. The script skips that section gracefully if they are absent.

## Method note (short version)

The only projection in this analysis concerns pupils, and it rests on already recorded births: the six birth cohorts matched to each school year were selected empirically by testing three alternatives against known enrolments (mean absolute error 3.2%).

For teachers, the analysis is descriptive. Survival ratios between five-year age bands are **measured**, not modelled — because the bands are five years wide, comparing two years five years apart maps the same cohort onto the next band exactly. No numerical forecast of departures is given; the reasons are documented. Full methodology, limitations and sources: [`docs/methodology.md`](docs/methodology.md).

## License

Code: MIT. Data remain subject to the terms of their respective sources (Eurostat, ELSTAT, Hellenic Ministry of Education).
